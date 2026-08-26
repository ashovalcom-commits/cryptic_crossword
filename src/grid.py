from enum import Enum
from typing import List, Tuple

class Direction(Enum):
    ACROSS = "across" # מאוזן
    DOWN = "down"     # מאונך

class Slot:
    def __init__(self, slot_id: int, row: int, col: int, length: int, direction: Direction):
        self.id = slot_id
        self.row = row
        self.col = col
        self.length = length
        self.direction = direction
        
        # לכאן נכניס את כל האילוצים. 
        # מבנה רשימה: (אינדקס האות שלי, Slot נחתך, אינדקס האות שלו)
        self.intersections: List[Tuple[int, 'Slot', int]] = []
        
        # בהמשך, כשנחבר את מאגר המילים, פה נשמור את "הדומיין" (המילים האפשריות)
        self.domain: List[str] = []

    def __repr__(self):
        return f"Slot_{self.id}({self.direction.name}, len={self.length}, pos=({self.row},{self.col}))"


class Grid:
    def __init__(self, layout: List[str], min_word_length: int = 3):
        """
        מקבל את תבנית הלוח.
        layout: רשימת מחרוזות, כאשר '.' זה תא חופשי ו-'#' זה תא שחור.
        """
        self.layout = layout
        self.rows = len(layout)
        self.cols = len(layout[0]) if self.rows > 0 else 0
        self.min_word_length = min_word_length
        self.slots: List[Slot] = []
        
        self._extract_slots()
        self._calculate_intersections()

    def _extract_slots(self):
        """
        סורק את הלוח ומוצא את כל המקומות החוקיים למילים (מאוזן ומאונך).
        """
        slot_id_counter = 0

        # סריקה 1: מציאת כל המילים המאוזנות (ACROSS) שורה אחר שורה
        for row in range(self.rows):
            col = 0
            while col < self.cols:
                if self.layout[row][col] == '.':
                    start_col = col
                    length = 0
                    # ממשיכים לספור כל עוד אנחנו על משבצת ריקה ולא חרגנו מהלוח
                    while col < self.cols and self.layout[row][col] == '.':
                        length += 1
                        col += 1
                    
                    # יצירת Slot רק אם הרצף ארוך מספיק (לפחות 3 אותיות כברירת מחדל)
                    if length >= self.min_word_length:
                        self.slots.append(Slot(slot_id_counter, row, start_col, length, Direction.ACROSS))
                        slot_id_counter += 1
                else:
                    col += 1 # מדלגים על משבצת שחורה (#)

        # סריקה 2: מציאת כל המילים המאונכות (DOWN) עמודה אחר עמודה
        for col in range(self.cols):
            row = 0
            while row < self.rows:
                if self.layout[row][col] == '.':
                    start_row = row
                    length = 0
                    # ממשיכים לספור למטה
                    while row < self.rows and self.layout[row][col] == '.':
                        length += 1
                        row += 1
                    
                    if length >= self.min_word_length:
                        self.slots.append(Slot(slot_id_counter, start_row, col, length, Direction.DOWN))
                        slot_id_counter += 1
                else:
                    row += 1

    def _calculate_intersections(self):
        """
        עובר על כל ה-Slots שחילצנו וממפה את נקודות החיתוך ביניהם.
        """
        pass # תכף נממש את זה

    def print_board(self):
        """
        פונקציית עזר להדפסת הלוח.
        """
        for row in self.layout:
            print(row)