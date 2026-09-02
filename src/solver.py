import argparse
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import random
from collections import defaultdict
from typing import List, Dict, Tuple
from grid import Grid, Slot
from parser import extract_text_from_docx, parse_grid_to_matrix, parse_clues, link_clues_to_grid

class Solver:
    def __init__(self, grid: Grid, wordbank_path: str):
        self.grid = grid
        self.wordbank_path = wordbank_path
        
        # מילון שבו המפתח הוא אורך המילה, והערך הוא רשימת המילים באורך הזה
        self.words_by_length: Dict[int, List[str]] = defaultdict(list)
        
        # מילון שבו המפתח הוא תבנית חלוקה למילים *ממוינת* (למשל (4, 6)), והערך
        # הוא רשימת המילים שאנחנו יודעים בוודאות שמתחלקות למילים באורכים האלה.
        # המפתח ממוין (ולא לפי הסדר המקורי) כי מקור התבנית במאגר (סדר המילים
        # בכותרת ויקיפדיה) לא בהכרח תואם לסדר שבו הן מופיעות בהגדרת התשבץ -
        # למשל "(5,4)" בהגדרה ו-"(4,5)" במאגר מתארים בפועל את אותה חלוקה.
        # תבנית זו נשמרת במאגר רק עבור ערכים שהגיעו במקור כמה מילים (עם רווח),
        # כדי שנוכל לסנן הצעות עבור הגדרות מפוצלות כמו "(4,6)" ולא להציע מילה
        # בודדת שרק סך אותיותיה מתאים, כמו "(7,3)".
        self.words_by_pattern: Dict[Tuple[int, ...], List[str]] = defaultdict(list)
        
        self._load_words()
        self._initialize_domains()

    def _load_words(self):
        """
        קורא את קובץ הנתונים וממפה את כל הערכים החוקיים לפי האורך שלהם,
        ולפי תבנית החלוקה למילים שלהם כשזו ידועה (עמודה שנייה מופרדת בטאב).
        """
        if not os.path.exists(self.wordbank_path):
            raise FileNotFoundError(f"לא נמצא קובץ נתונים בנתיב: {self.wordbank_path}")
            
        with open(self.wordbank_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if not line:
                    continue
                
                if '\t' in line:
                    word, pattern_str = line.split('\t', 1)
                    word = word.strip()
                    pattern = tuple(int(p) for p in pattern_str.split(',') if p.strip())
                else:
                    word = line.strip()
                    pattern = ()
                
                if not word:
                    continue
                
                self.words_by_length[len(word)].append(word)
                if len(pattern) > 1:
                    self.words_by_pattern[tuple(sorted(pattern))].append(word)
        
        # הדפסת בקרה קטנה לראות שהכל נטען
        total_words = sum(len(words) for words in self.words_by_length.values())
        print(f"נטענו {total_words:,} מילים למנוע השיבוץ.")

    def _initialize_domains(self):
        """
        מזין לכל Slot בלוח את מרחב האפשרויות ההתחלתי שלו.
        אם להגדרה יש תבנית חלוקה למילים ידועה (כמו "(4,6)"), מסננים מראש
        רק למילים שידוע שמתחלקות בדיוק כך - כדי לא להציע התאמות שגויות
        כמו מילה שסך אותיותיה מתאים אך החלוקה שלה שונה (למשל "(7,3)" במקום "(4,6)").
        """
        for slot in self.grid.slots:
            if len(slot.clue_word_lengths) > 1:
                pattern = tuple(sorted(slot.clue_word_lengths))
                slot.domain = self.words_by_pattern.get(pattern, []).copy()
            else:
                # אנחנו שומרים עותק (copy) של הרשימה. 
                # זה קריטי כדי שנוכל למחוק מילים שנפסלו מ-Slot אחד בלי למחוק אותן מהמאגר הכללי.
                slot.domain = self.words_by_length.get(slot.length, []).copy()

            # מערבבים את רשימת המילים כדי לקבל תוצאה שונה בכל הרצה
            random.shuffle(slot.domain)
            
            if not slot.domain:
                print(f"אזהרה: לא נמצאו מילים באורך {slot.length} עבור Slot {slot.id}!")


    def solve(self) -> bool:
        """
        פונקציית המעטפת שמתחילה את הרקורסיה.
        """
        print("מתחיל אלגוריתם שיבוץ עם MRV...")
        # אנחנו כבר לא מעבירים אינדקס!
        return self._backtrack()

    def _get_unassigned_mrv_slot(self):
        """
        סורק את כל העוגנים הפנויים ומחזיר את זה שיש לו הכי מעט מילים חוקיות כרגע.
        """
        best_slot = None
        min_remaining = float('inf')
        
        for slot in self.grid.slots:
            if slot.assigned_word is None:
                # סופרים כמה מילים חוקיות נשארו לעוגן במצב הלוח הנוכחי
                valid_count = sum(1 for word in slot.domain if self._is_valid_assignment(slot, word))
                
                if valid_count < min_remaining:
                    min_remaining = valid_count
                    best_slot = slot
                    
        return best_slot

    def _backtrack(self) -> bool:
        """
        פונקציה רקורסיבית מונחית MRV.
        """
        # בוחרים את העוגן הכי "לחוץ" (זה עם הכי מעט אפשרויות)
        current_slot = self._get_unassigned_mrv_slot()
        
        # תנאי עצירה: אם הפונקציה לא מצאה אף עוגן פנוי, סימן שכולם מלאים וסיימנו!
        if current_slot is None:
            return True

        # מייצרים רשימה רק של המילים שחוקיות כרגע, כדי לחסוך קריאות רקורסיביות שייכשלו
        valid_words = [word for word in current_slot.domain if self._is_valid_assignment(current_slot, word)]

        for word in valid_words:
            current_slot.assigned_word = word

            if self._backtrack():
                return True

            current_slot.assigned_word = None

        return False

    def _is_valid_assignment(self, slot: Slot, word: str) -> bool:
        """
        בודקת האם מילה מסוימת יכולה להיכנס לעוגן מבלי לייצר התנגשויות.
        """
        # בדיקה 1: כפילויות. לא רוצים את אותה מילה פעמיים בתשבץ
        for s in self.grid.slots:
            if s.assigned_word == word:
                return False

        # בדיקה 2: התנגשות חיתוכים
        for my_idx, other_slot, other_idx in slot.intersections:
            if other_slot.assigned_word is not None:
                # אם העוגן שחותך אותנו כבר קיבל מילה, האות בנקודת המפגש חייבת להיות זהה
                if word[my_idx] != other_slot.assigned_word[other_idx]:
                    return False

        return True

    def plot_solution(self):
        """
        מצייר את התשבץ כגרף ויזואלי בעזרת Matplotlib.
        """
        # בניית מטריצת התשבץ המלאה
        board = [['#' if cell == '#' else ' ' for cell in row] for row in self.grid.layout]
        for slot in self.grid.slots:
            if slot.assigned_word:
                for i, char in enumerate(slot.assigned_word):
                    if slot.direction.name == "ACROSS":
                        board[slot.row][slot.col + i] = char
                    else:
                        board[slot.row + i][slot.col] = char

        # הגדרת הגרף
        fig, ax = plt.subplots(figsize=(self.grid.cols, self.grid.rows))
        
        # ציור המשבצות והאותיות
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                char = board[r][c]
                
                # קביעת צבע המשבצת
                facecolor = 'black' if char == '#' else 'white'
                
                # ציור ריבוע המשבצת
                rect = patches.Rectangle((c, r), 1, 1, facecolor=facecolor, edgecolor='black', linewidth=2)
                ax.add_patch(rect)
                
                # הוספת האות אם ישנה
                if char not in ['#', ' ']:
                    ax.text(c + 0.5, r + 0.5, char, ha='center', va='center', 
                            fontsize=24, fontweight='bold', color='black')

        # הגדרת גבולות הצירים לפי גודל הלוח
        ax.set_xlim(0, self.grid.cols)
        ax.set_ylim(0, self.grid.rows)
        
        # שמירה על פרופורציות ריבועיות
        ax.set_aspect('equal')
        
        # התאמות כיווניות: 
        ax.invert_yaxis()  # שורה 0 למעלה (כמו במטריצה)
        ax.invert_xaxis()  # עמודה 0 בצד ימין (קריאה מימין לשמאל לעברית)
        
        # העלמת המספרים של הצירים
        ax.axis('off')
        
        # הצגת החלון
        plt.title("Cryptic Crossword Generated Solution", fontsize=16)
        plt.tight_layout()
        plt.show()

    def get_slot_by_clue(self, clue_number: str, direction_name: str):
        """
        שולף עוגן ספציפי מהלוח לפי מספר ההגדרה והכיוון (ACROSS/DOWN).
        """
        for slot in self.grid.slots:
            if slot.clue_number == str(clue_number) and slot.direction.name == direction_name:
                return slot
        return None

    def lock_word(self, clue_number: str, direction_name: str, word: str):
        """
        מדמה פעולה של פותר אנושי: נועל מילה ספציפית בעוגן.
        """
        slot = self.get_slot_by_clue(clue_number, direction_name)
        if slot:
            if len(word) == slot.length:
                slot.assigned_word = word
                print(f"ננעל: {word} בהגדרה {clue_number} {direction_name}")
            else:
                print(f"שגיאה: המילה '{word}' באורך {len(word)}, אבל העוגן דורש {slot.length} אותיות.")
        else:
            print(f"לא נמצא עוגן {clue_number} {direction_name}")

    def unlock_word(self, clue_number: str, direction_name: str):
        """
        משחרר מילה שנועלה בעוגן ומחזיר אותו למצב פנוי.
        """
        slot = self.get_slot_by_clue(clue_number, direction_name)
        if slot:
            if slot.assigned_word:
                old_word = slot.assigned_word
                slot.assigned_word = None
                print(f"שוחרר: '{old_word}' מהגדרה {clue_number} {direction_name}")
            else:
                print(f"העוגן {clue_number} {direction_name} כבר פנוי.")
        else:
            print(f"לא נמצא עוגן {clue_number} {direction_name}")

    def solve_slot(self, clue_number: str, direction_name: str) -> bool:
        """
        מנסה למצוא מילה חוקית לעוגן ספציפי בהתחשב במצב הנוכחי של הלוח.
        מחזיר True אם נמצאה מילה, False אחרת.
        """
        slot = self.get_slot_by_clue(clue_number, direction_name)
        if not slot:
            print(f"לא נמצא עוגן {clue_number} {direction_name}")
            return False

        if slot.assigned_word:
            print(f"העוגן {clue_number} {direction_name} כבר מכיל: '{slot.assigned_word}'")
            return True

        valid_words = [w for w in slot.domain if self._is_valid_assignment(slot, w)]
        if not valid_words:
            print(f"לא נמצאו מילים חוקיות עבור {clue_number} {direction_name} במצב הנוכחי של הלוח.")
            return False

        # שיבוץ המילה הראשונה שעוברת את כל האילוצים
        slot.assigned_word = valid_words[0]
        dir_he = "אופקי" if direction_name == "ACROSS" else "אנכי"
        print(f"שובץ: '{valid_words[0]}' בהגדרה {clue_number} {dir_he} (מתוך {len(valid_words)} אפשרויות)")
        return True

    def suggest_words_for_slot(self, clue_number: str, direction_name: str, max_results: int = 10) -> List[str]:
        """
        מחזיר רשימת מילים חוקיות מהמילון עבור עוגן ספציפי, בהתבסס על החיתוכים הקיימים בלוח.
        """
        slot = self.get_slot_by_clue(clue_number, direction_name)
        if not slot:
            return []
            
        # סינון המילים בדומיין של העוגן לפי המצב הנוכחי של הלוח
        valid_words = [word for word in slot.domain if self._is_valid_assignment(slot, word)]
        return valid_words[:max_results]

    def print_board(self):
        """
        מציג את מצב הלוח הנוכחי בטקסט - כולל אותיות שכבר שובצו.
        """
        board = [['█' if cell == '#' else '.' for cell in row] for row in self.grid.layout]
        for slot in self.grid.slots:
            if slot.assigned_word:
                for i, char in enumerate(slot.assigned_word):
                    if slot.direction.name == "ACROSS":
                        board[slot.row][slot.col + i] = char
                    else:
                        board[slot.row + i][slot.col] = char

        filled = sum(1 for slot in self.grid.slots if slot.assigned_word)
        total = len(self.grid.slots)
        print(f"\n--- מצב הלוח ({filled}/{total} הגדרות פתורות) ---")
        for row in board:
            print(' '.join(row))
        print()

    def list_clues(self):
        """
        מציג את כל ההגדרות בלוח עם הסטטוס שלהן (פתור / פנוי).
        """
        print("\n--- אופקי ---")
        across = sorted(
            [s for s in self.grid.slots if s.direction.name == "ACROSS" and s.clue_number],
            key=lambda s: int(s.clue_number)
        )
        for slot in across:
            status = f"✓ {slot.assigned_word}" if slot.assigned_word else f"_ ({slot.length} אותיות)"
            clue = slot.clue_text if slot.clue_text else "(ללא הגדרה)"
            print(f"  {slot.clue_number}. {clue}  [{status}]")

        print("\n--- אנכי ---")
        down = sorted(
            [s for s in self.grid.slots if s.direction.name == "DOWN" and s.clue_number],
            key=lambda s: int(s.clue_number)
        )
        for slot in down:
            status = f"✓ {slot.assigned_word}" if slot.assigned_word else f"_ ({slot.length} אותיות)"
            clue = slot.clue_text if slot.clue_text else "(ללא הגדרה)"
            print(f"  {slot.clue_number}. {clue}  [{status}]")
        print()

    def _parse_direction_input(self, dir_str: str) -> str:
        """
        ממיר קלט כיוון בעברית או באנגלית לערך פנימי.
        """
        dir_str = dir_str.strip().lower()
        if dir_str in ('אופקי', 'across', 'a', 'א'):
            return "ACROSS"
        elif dir_str in ('אנכי', 'down', 'd', 'מ'):
            return "DOWN"
        return ""

    def run_interactive(self):
        """
        לולאה אינטראקטיבית שמאפשרת למשתמש לעבוד עם התשבץ צעד אחר צעד.
        """
        print("\n" + "=" * 50)
        print("  פותר תשבצים אינטראקטיבי")
        print("=" * 50)
        self.print_board()

        help_text = """
פקודות זמינות:
  הגדרות / ה       - הצגת כל ההגדרות והסטטוס שלהן
  לוח / ל          - הצגת מצב הלוח
  נעל / נ          - נעילת מילה (שאתה כבר פתרת)
  שחרר / ש         - שחרור מילה שנעלת
  הצע / צ          - הצעת מילים אפשריות להגדרה
  פתור / פ         - המנוע ינסה לפתור הגדרה ספציפית
  ציור             - הצגת הלוח הגרפי (Matplotlib)
  עזרה / ?         - הצגת תפריט זה
  יציאה / י        - יציאה מהתוכנית
"""
        print(help_text)

        while True:
            try:
                user_input = input(">> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nלהתראות!")
                break

            if not user_input:
                continue

            cmd = user_input.split()[0]

            if cmd in ('יציאה', 'י', 'exit', 'q'):
                print("להתראות!")
                break

            elif cmd in ('עזרה', '?', 'help'):
                print(help_text)

            elif cmd in ('לוח', 'ל', 'board'):
                self.print_board()

            elif cmd in ('הגדרות', 'ה', 'clues'):
                self.list_clues()

            elif cmd in ('ציור', 'plot'):
                self.plot_solution()

            elif cmd in ('נעל', 'נ', 'lock'):
                try:
                    num = input("  מספר הגדרה: ").strip()
                    direction = input("  כיוון (אופקי/אנכי): ").strip()
                    word = input("  מילה: ").strip()
                    dir_name = self._parse_direction_input(direction)
                    if not dir_name:
                        print("  כיוון לא תקין. השתמש ב-'אופקי' או 'אנכי'.")
                        continue
                    self.lock_word(num, dir_name, word)
                except (EOFError, KeyboardInterrupt):
                    print()
                    continue

            elif cmd in ('שחרר', 'ש', 'unlock'):
                try:
                    num = input("  מספר הגדרה: ").strip()
                    direction = input("  כיוון (אופקי/אנכי): ").strip()
                    dir_name = self._parse_direction_input(direction)
                    if not dir_name:
                        print("  כיוון לא תקין. השתמש ב-'אופקי' או 'אנכי'.")
                        continue
                    self.unlock_word(num, dir_name)
                except (EOFError, KeyboardInterrupt):
                    print()
                    continue

            elif cmd in ('הצע', 'צ', 'suggest'):
                try:
                    num = input("  מספר הגדרה: ").strip()
                    direction = input("  כיוון (אופקי/אנכי): ").strip()
                    dir_name = self._parse_direction_input(direction)
                    if not dir_name:
                        print("  כיוון לא תקין. השתמש ב-'אופקי' או 'אנכי'.")
                        continue
                    suggestions = self.suggest_words_for_slot(num, dir_name, max_results=15)
                    if suggestions:
                        slot = self.get_slot_by_clue(num, dir_name)
                        dir_he = "אופקי" if dir_name == "ACROSS" else "אנכי"
                        print(f"  הצעות עבור {num} {dir_he} ({slot.length} אותיות):")
                        for i, w in enumerate(suggestions, 1):
                            print(f"    {i}. {w}")
                    else:
                        print("  לא נמצאו מילים מתאימות במצב הנוכחי.")
                except (EOFError, KeyboardInterrupt):
                    print()
                    continue

            elif cmd in ('פתור', 'פ', 'solve'):
                try:
                    num = input("  מספר הגדרה: ").strip()
                    direction = input("  כיוון (אופקי/אנכי): ").strip()
                    dir_name = self._parse_direction_input(direction)
                    if not dir_name:
                        print("  כיוון לא תקין. השתמש ב-'אופקי' או 'אנכי'.")
                        continue
                    self.solve_slot(num, dir_name)
                except (EOFError, KeyboardInterrupt):
                    print()
                    continue

            else:
                print("  פקודה לא מוכרת. הקלד 'עזרה' לרשימת הפקודות.")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="פותר תשבצים קריפטיים אינטראקטיבי")
    arg_parser.add_argument("docx_path", help="נתיב לקובץ ה-DOCX של התשבץ")
    arg_parser.add_argument("--wordbank", default="data/crossword_wordbank_he.txt",
                            help="נתיב לקובץ מאגר המילים (ברירת מחדל: data/crossword_wordbank_he.txt)")
    arg_parser.add_argument("--min-length", type=int, default=2,
                            help="אורך מילה מינימלי (ברירת מחדל: 2)")
    args = arg_parser.parse_args()

    try:
        # 1. טעינה ופענוח הלוח
        raw_text = extract_text_from_docx(args.docx_path)
        result_matrix = parse_grid_to_matrix(raw_text)
        parsed_clues = parse_clues(raw_text)

        my_grid = Grid(result_matrix, min_word_length=args.min_length)
        link_clues_to_grid(my_grid, parsed_clues)

        # 2. יצירת הפותרן והפעלת מצב אינטראקטיבי
        my_solver = Solver(my_grid, args.wordbank)
        my_solver.run_interactive()

    except Exception as e:
        print(f"שגיאה בהרצה: {e}")