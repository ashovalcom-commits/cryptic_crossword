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
        self.assigned_word = None
        # המאפיינים החדשים שיחזיקו את נתוני ההגדרה
        self.clue_number: str = ""
        self.clue_text: str = ""
        
        # לכאן נכניס את כל האילוצים. 
        # מבנה רשימה: (אינדקס האות שלי, Slot נחתך, אינדקס האות שלו)
        self.intersections: List[Tuple[int, 'Slot', int]] = []
        
        # בהמשך, כשנחבר את מאגר המילים, פה נשמור את "הדומיין" (המילים האפשריות)
        self.domain: List[str] = []

    def __repr__(self):
        return f"Slot_{self.id}({self.direction.name}, len={self.length}, pos=({self.row},{self.col}))"


class Grid:
    def __init__(self, layout: List[str], min_word_length: int = 3):
        self.layout = layout
        self.rows = len(layout)
        self.cols = len(layout[0]) if self.rows > 0 else 0
        self.min_word_length = min_word_length
        self.slots: List[Slot] = []
        
        self._extract_slots()
        self._calculate_intersections()

    def _extract_slots(self):
        slot_id_counter = 0

        # סריקה 1: מאוזן
        for row in range(self.rows):
            col = 0
            while col < self.cols:
                if self.layout[row][col] != '#':
                    start_col = col
                    length = 0
                    
                    cell_val = str(self.layout[row][col]).strip()
                    clue_num = cell_val if cell_val.isdigit() else ""
                    
                    while col < self.cols and self.layout[row][col] != '#':
                        length += 1
                        col += 1
                    
                    if length >= self.min_word_length:
                        new_slot = Slot(slot_id_counter, row, start_col, length, Direction.ACROSS)
                        new_slot.clue_number = clue_num
                        self.slots.append(new_slot)
                        slot_id_counter += 1
                else:
                    col += 1

        # סריקה 2: מאונך
        for col in range(self.cols):
            row = 0
            while row < self.rows:
                if self.layout[row][col] != '#':
                    start_row = row
                    length = 0
                    
                    cell_val = str(self.layout[row][col]).strip()
                    clue_num = cell_val if cell_val.isdigit() else ""
                    
                    while row < self.rows and self.layout[row][col] != '#':
                        length += 1
                        row += 1
                    
                    if length >= self.min_word_length:
                        new_slot = Slot(slot_id_counter, start_row, col, length, Direction.DOWN)
                        new_slot.clue_number = clue_num
                        self.slots.append(new_slot)
                        slot_id_counter += 1
                else:
                    row += 1

    def _calculate_intersections(self):
        across_slots = [s for s in self.slots if s.direction == Direction.ACROSS]
        down_slots = [s for s in self.slots if s.direction == Direction.DOWN]

        for a_slot in across_slots:
            for d_slot in down_slots:
                if (a_slot.col <= d_slot.col < a_slot.col + a_slot.length) and \
                   (d_slot.row <= a_slot.row < d_slot.row + d_slot.length):
                    
                    a_index = d_slot.col - a_slot.col
                    d_index = a_slot.row - d_slot.row
                    
                    a_slot.intersections.append((a_index, d_slot, d_index))
                    d_slot.intersections.append((d_index, a_slot, a_index))

    def print_board(self):
        for row in self.layout:
            print(row)


if __name__ == "__main__":
    # נגדיר לוח קטן לבדיקה: שתי מילים מאוזנות ושתי מילים מאונכות
    test_layout = [
        "....",
        ".##.",
        "....",
        ".##."
    ]
    
    # יוצרים את הלוח (זה יפעיל אוטומטית את שתי הפונקציות שכתבנו)
    my_grid = Grid(test_layout, min_word_length=3)
    
    print(f"Total slots found: {len(my_grid.slots)}")
    for slot in my_grid.slots:
        print(slot)
        for my_idx, other_slot, other_idx in slot.intersections:
            print(f"  -> Intersects with {other_slot.id} at index {my_idx} (their index {other_idx})")