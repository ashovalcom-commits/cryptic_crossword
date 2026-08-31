import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import random
from collections import defaultdict
from typing import List, Dict
from grid import Grid, Slot
from parser import extract_text_from_docx, parse_grid_to_matrix, parse_clues, link_clues_to_grid

class Solver:
    def __init__(self, grid: Grid, wordbank_path: str):
        self.grid = grid
        self.wordbank_path = wordbank_path
        
        # מילון שבו המפתח הוא אורך המילה, והערך הוא רשימת המילים באורך הזה
        self.words_by_length: Dict[int, List[str]] = defaultdict(list)
        
        self._load_words()
        self._initialize_domains()

    def _load_words(self):
        """
        קורא את קובץ הנתונים וממפה את כל הערכים החוקיים לפי האורך שלהם.
        """
        if not os.path.exists(self.wordbank_path):
            raise FileNotFoundError(f"לא נמצא קובץ נתונים בנתיב: {self.wordbank_path}")
            
        with open(self.wordbank_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip()
                if word:
                    self.words_by_length[len(word)].append(word)
        
        # הדפסת בקרה קטנה לראות שהכל נטען
        total_words = sum(len(words) for words in self.words_by_length.values())
        print(f"נטענו {total_words:,} מילים למנוע השיבוץ.")

    def _initialize_domains(self):
        """
        מזין לכל Slot בלוח את מרחב האפשרויות ההתחלתי שלו.
        """
        for slot in self.grid.slots:
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



if __name__ == "__main__":
    # שימוש בקובץ האמיתי מתוך ה-parser
    file_path = r"C:\Users\ashov\Downloads\28-08-26.docx"
    wordbank = "data/crossword_wordbank_he.txt"
    
    try:
        # 1. טעינה ופענוח הלוח
        raw_text = extract_text_from_docx(file_path)
        result_matrix = parse_grid_to_matrix(raw_text)
        parsed_clues = parse_clues(raw_text)
        
        my_grid = Grid(result_matrix, min_word_length=2)
        link_clues_to_grid(my_grid, parsed_clues)
        
        # 2. יצירת הפותרן
        my_solver = Solver(my_grid, wordbank)
        
        print("\n--- סימולציית פתרון אינטראקטיבי ---")
        # נניח שפתרת את 9 אופקי: "קצין עם קוף (3)" -> סרן (סרן + ן')
        my_solver.lock_word("9", "ACROSS", "סרן")
        
        # עכשיו נבקש מהמערכת עזרה עם 1 מאונך שחותך את המילה שהזנו
        clue_1_down = my_solver.get_slot_by_clue("1", "DOWN")
        print(f"\nמבקש הצעות עבור {clue_1_down.clue_number} מאונך: '{clue_1_down.clue_text}'")
        
        suggestions = my_solver.suggest_words_for_slot("1", "DOWN", max_results=5)
        print(f"הצעות המנוע (מתוך המילון, מתחשב באות 'ס' שנחתכת): {suggestions}")
        
        # הצגת הלוח החלקי כדי לראות את המילה ששובצה
        my_solver.plot_solution()
        
    except Exception as e:
        print(f"שגיאה בהרצה: {e}")