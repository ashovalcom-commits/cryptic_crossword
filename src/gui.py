import argparse
import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from grid import Grid, Slot, Direction
from parser import extract_text_from_docx, parse_grid_to_matrix, parse_clues, link_clues_to_grid
from solver import Solver


# ─── Constants ───────────────────────────────────────────────────────────────
CELL_SIZE = 44
FONT_LETTER = ("Arial", 18, "bold")
FONT_CLUE_NUM = ("Arial", 8)
COLOR_BLACK = "#1a1a1a"
COLOR_WHITE = "#ffffff"
COLOR_SELECTED = "#b3d9ff"
COLOR_HIGHLIGHT = "#d4edda"
COLOR_BORDER = "#333333"


class CrosswordGUI:
    def __init__(self, root: tk.Tk, solver: Solver):
        self.root = root
        self.solver = solver
        self.grid = solver.grid
        self.selected_slot: Slot | None = None

        self.root.title("פותר תשבצים קריפטיים")
        self.root.configure(bg="#f0f0f0")

        self._build_ui()
        self._draw_board()
        self._populate_clues()

    # ─── UI Construction ─────────────────────────────────────────────────

    def _build_ui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Allow the clues column to expand when the window is resized
        main_frame.columnconfigure(0, weight=1)

        # Left: crossword canvas
        canvas_width = self.grid.cols * CELL_SIZE + 2
        canvas_height = self.grid.rows * CELL_SIZE + 2
        self.canvas = tk.Canvas(
            main_frame, width=canvas_width, height=canvas_height,
            bg=COLOR_WHITE, highlightthickness=1, highlightbackground=COLOR_BORDER
        )
        self.canvas.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="n")
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # Right: clues panel (RTL order - clues on the right)
        clues_frame = ttk.Frame(main_frame)
        clues_frame.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="nsew")

        # Across clues
        ttk.Label(clues_frame, text="אופקי", font=("Arial", 12, "bold")).pack(anchor="e", pady=(0, 2))
        across_frame = ttk.Frame(clues_frame)
        across_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        self.across_listbox = tk.Listbox(
            across_frame, font=("Arial", 10), width=70, height=10,
            selectmode=tk.SINGLE, justify=tk.RIGHT
        )
        across_scroll_y = ttk.Scrollbar(across_frame, orient=tk.VERTICAL, command=self.across_listbox.yview)
        across_scroll_x = ttk.Scrollbar(across_frame, orient=tk.HORIZONTAL, command=self.across_listbox.xview)
        self.across_listbox.configure(yscrollcommand=across_scroll_y.set, xscrollcommand=across_scroll_x.set)
        across_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        across_scroll_y.pack(side=tk.LEFT, fill=tk.Y)
        self.across_listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.across_listbox.bind("<<ListboxSelect>>", lambda e: self._on_clue_select("ACROSS"))

        # Down clues
        ttk.Label(clues_frame, text="אנכי", font=("Arial", 12, "bold")).pack(anchor="e", pady=(0, 2))
        down_frame = ttk.Frame(clues_frame)
        down_frame.pack(fill=tk.BOTH, expand=True)

        self.down_listbox = tk.Listbox(
            down_frame, font=("Arial", 10), width=70, height=10,
            selectmode=tk.SINGLE, justify=tk.RIGHT
        )
        down_scroll_y = ttk.Scrollbar(down_frame, orient=tk.VERTICAL, command=self.down_listbox.yview)
        down_scroll_x = ttk.Scrollbar(down_frame, orient=tk.HORIZONTAL, command=self.down_listbox.xview)
        self.down_listbox.configure(yscrollcommand=down_scroll_y.set, xscrollcommand=down_scroll_x.set)
        down_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        down_scroll_y.pack(side=tk.LEFT, fill=tk.Y)
        self.down_listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.down_listbox.bind("<<ListboxSelect>>", lambda e: self._on_clue_select("DOWN"))

        # Bottom: action panel
        action_frame = ttk.LabelFrame(main_frame, text="פעולות", padding=8)
        action_frame.grid(row=1, column=0, columnspan=2, pady=(8, 0), sticky="ew")

        # Word entry row
        entry_row = ttk.Frame(action_frame)
        entry_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Button(entry_row, text="נעל מילה", command=self._lock_word).pack(side=tk.RIGHT, padx=4)
        self.word_entry = ttk.Entry(entry_row, font=("Arial", 14), width=20, justify=tk.RIGHT)
        self.word_entry.pack(side=tk.RIGHT, padx=4)
        ttk.Label(entry_row, text=":מילה", font=("Arial", 10)).pack(side=tk.RIGHT, padx=4)

        ttk.Button(entry_row, text="שחרר", command=self._unlock_word).pack(side=tk.RIGHT, padx=4)

        # Buttons row
        btn_row = ttk.Frame(action_frame)
        btn_row.pack(fill=tk.X)

        ttk.Button(btn_row, text="פתור הגדרה", command=self._solve_selected).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btn_row, text="הצע מילים", command=self._suggest_words).pack(side=tk.RIGHT, padx=4)

        # Selected clue display
        self.selected_label = ttk.Label(
            action_frame, text="בחר הגדרה מהרשימה או לחץ על הלוח",
            font=("Arial", 11), foreground="#555555"
        )
        self.selected_label.pack(anchor="e", pady=(6, 0))

        # Suggestions list
        self.suggestions_frame = ttk.LabelFrame(main_frame, text="הצעות", padding=5)
        self.suggestions_frame.grid(row=2, column=0, columnspan=2, pady=(6, 0), sticky="ew")

        self.suggestions_listbox = tk.Listbox(
            self.suggestions_frame, font=("Arial", 11), height=5,
            selectmode=tk.SINGLE, justify=tk.RIGHT
        )
        self.suggestions_listbox.pack(fill=tk.BOTH, expand=True)
        self.suggestions_listbox.bind("<Double-Button-1>", self._on_suggestion_double_click)

        # Status bar
        self.status_var = tk.StringVar(value="מוכן")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor="e")
        status_bar.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        # Keyboard binding
        self.root.bind("<Return>", lambda e: self._lock_word())

    # ─── Board Drawing ───────────────────────────────────────────────────

    def _build_board_matrix(self) -> list:
        """Build the current board state as a 2D char matrix."""
        board = [['#' if cell == '#' else '' for cell in row] for row in self.grid.layout]
        for slot in self.grid.slots:
            if slot.assigned_word:
                for i, char in enumerate(slot.assigned_word):
                    if slot.direction == Direction.ACROSS:
                        board[slot.row][slot.col + i] = char
                    else:
                        board[slot.row + i][slot.col] = char
        return board

    def _get_clue_numbers_map(self) -> dict:
        """Return dict mapping (row, col) -> clue number for first cells of slots."""
        nums = {}
        for slot in self.grid.slots:
            if slot.clue_number:
                pos = (slot.row, slot.col)
                if pos not in nums:
                    nums[pos] = slot.clue_number
        return nums

    def _get_selected_cells(self) -> set:
        """Return set of (row, col) for the currently selected slot."""
        if not self.selected_slot:
            return set()
        cells = set()
        s = self.selected_slot
        for i in range(s.length):
            if s.direction == Direction.ACROSS:
                cells.add((s.row, s.col + i))
            else:
                cells.add((s.row + i, s.col))
        return cells

    def _draw_board(self):
        self.canvas.delete("all")
        board = self._build_board_matrix()
        clue_nums = self._get_clue_numbers_map()
        selected_cells = self._get_selected_cells()

        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                # RTL: mirror x so column 0 is on the right
                x = (self.grid.cols - 1 - c) * CELL_SIZE
                y = r * CELL_SIZE
                cell = board[r][c]

                if cell == '#':
                    fill = COLOR_BLACK
                elif (r, c) in selected_cells:
                    fill = COLOR_SELECTED
                else:
                    fill = COLOR_WHITE

                self.canvas.create_rectangle(
                    x, y, x + CELL_SIZE, y + CELL_SIZE,
                    fill=fill, outline=COLOR_BORDER, width=1.5
                )

                # Draw letter
                if cell and cell != '#':
                    self.canvas.create_text(
                        x + CELL_SIZE / 2, y + CELL_SIZE / 2,
                        text=cell, font=FONT_LETTER, fill="black"
                    )

                # Draw clue number (top-right corner in RTL)
                if (r, c) in clue_nums:
                    self.canvas.create_text(
                        x + CELL_SIZE - 4, y + 4,
                        text=clue_nums[(r, c)], font=FONT_CLUE_NUM,
                        fill="#666666", anchor="ne"
                    )

    # ─── Clue Panel ──────────────────────────────────────────────────────

    def _clue_display_text(self, slot: Slot) -> str:
        status = f"✓ {slot.assigned_word}" if slot.assigned_word else f"({slot.length})"
        clue = slot.clue_text if slot.clue_text else ""
        return f"{slot.clue_number}. {clue}  [{status}]"

    def _populate_clues(self):
        self.across_listbox.delete(0, tk.END)
        self.down_listbox.delete(0, tk.END)

        self._across_slots = sorted(
            [s for s in self.grid.slots if s.direction == Direction.ACROSS and s.clue_number],
            key=lambda s: int(s.clue_number)
        )
        self._down_slots = sorted(
            [s for s in self.grid.slots if s.direction == Direction.DOWN and s.clue_number],
            key=lambda s: int(s.clue_number)
        )

        for slot in self._across_slots:
            self.across_listbox.insert(tk.END, self._clue_display_text(slot))
            if slot.assigned_word:
                self.across_listbox.itemconfig(tk.END, fg="#2e7d32")

        for slot in self._down_slots:
            self.down_listbox.insert(tk.END, self._clue_display_text(slot))
            if slot.assigned_word:
                self.down_listbox.itemconfig(tk.END, fg="#2e7d32")

    def _refresh(self):
        """Redraw board and repopulate clue lists."""
        self._draw_board()
        self._populate_clues()
        self._update_status()

    def _update_status(self):
        filled = sum(1 for s in self.grid.slots if s.assigned_word)
        total = len(self.grid.slots)
        self.status_var.set(f"הגדרות פתורות: {filled}/{total}")

    def _update_selected_label(self):
        if self.selected_slot:
            s = self.selected_slot
            dir_he = "אופקי" if s.direction == Direction.ACROSS else "אנכי"
            clue = s.clue_text if s.clue_text else "(ללא הגדרה)"
            word_info = f" → {s.assigned_word}" if s.assigned_word else f" ({s.length} אותיות)"
            self.selected_label.config(
                text=f"{s.clue_number} {dir_he}: {clue}{word_info}",
                foreground="#000000"
            )
        else:
            self.selected_label.config(
                text="בחר הגדרה מהרשימה או לחץ על הלוח",
                foreground="#555555"
            )

    # ─── Event Handlers ──────────────────────────────────────────────────

    def _on_canvas_click(self, event):
        # RTL: reverse the x coordinate
        col = self.grid.cols - 1 - int(event.x // CELL_SIZE)
        row = int(event.y // CELL_SIZE)

        if col < 0 or col >= self.grid.cols or row < 0 or row >= self.grid.rows:
            return
        if self.grid.layout[row][col] == '#':
            return

        # Find a slot that contains this cell, prefer one that isn't the currently selected
        candidates = []
        for slot in self.grid.slots:
            if slot.direction == Direction.ACROSS and slot.row == row \
               and slot.col <= col < slot.col + slot.length:
                candidates.append(slot)
            elif slot.direction == Direction.DOWN and slot.col == col \
                 and slot.row <= row < slot.row + slot.length:
                candidates.append(slot)

        if not candidates:
            return

        # Toggle direction if clicking the same cell again
        if self.selected_slot in candidates and len(candidates) > 1:
            candidates.remove(self.selected_slot)

        self.selected_slot = candidates[0]
        self._update_selected_label()
        self._draw_board()
        self.word_entry.focus_set()

    def _on_clue_select(self, direction: str):
        if direction == "ACROSS":
            sel = self.across_listbox.curselection()
            if sel:
                self.selected_slot = self._across_slots[sel[0]]
                self.down_listbox.selection_clear(0, tk.END)
        else:
            sel = self.down_listbox.curselection()
            if sel:
                self.selected_slot = self._down_slots[sel[0]]
                self.across_listbox.selection_clear(0, tk.END)

        self._update_selected_label()
        self._draw_board()
        self.word_entry.focus_set()

    def _on_suggestion_double_click(self, event):
        sel = self.suggestions_listbox.curselection()
        if sel and self.selected_slot:
            word = self.suggestions_listbox.get(sel[0])
            self.word_entry.delete(0, tk.END)
            self.word_entry.insert(0, word)
            self._lock_word()

    # ─── Actions ─────────────────────────────────────────────────────────

    def _lock_word(self):
        if not self.selected_slot:
            messagebox.showwarning("שגיאה", "בחר הגדרה קודם.")
            return

        word = self.word_entry.get().strip()
        if not word:
            messagebox.showwarning("שגיאה", "הכנס מילה.")
            return

        slot = self.selected_slot
        if len(word) != slot.length:
            messagebox.showwarning(
                "אורך שגוי",
                f"המילה '{word}' באורך {len(word)}, אבל ההגדרה דורשת {slot.length} אותיות."
            )
            return

        # Check for conflicts
        if not self.solver._is_valid_assignment(slot, word):
            result = messagebox.askyesno(
                "התנגשות",
                f"המילה '{word}' מתנגשת עם מילים קיימות בלוח.\nלנעול בכל זאת?"
            )
            if not result:
                return

        slot.assigned_word = word
        self.word_entry.delete(0, tk.END)
        self._refresh()
        self._update_selected_label()

    def _unlock_word(self):
        if not self.selected_slot:
            messagebox.showwarning("שגיאה", "בחר הגדרה קודם.")
            return

        if self.selected_slot.assigned_word:
            self.selected_slot.assigned_word = None
            self._refresh()
            self._update_selected_label()

    def _solve_selected(self):
        if not self.selected_slot:
            messagebox.showwarning("שגיאה", "בחר הגדרה קודם.")
            return

        slot = self.selected_slot
        if slot.assigned_word:
            messagebox.showinfo("מידע", f"ההגדרה כבר פתורה: '{slot.assigned_word}'")
            return

        valid_words = [w for w in slot.domain if self.solver._is_valid_assignment(slot, w)]
        if not valid_words:
            messagebox.showinfo("לא נמצא", "לא נמצאו מילים חוקיות במצב הנוכחי של הלוח.")
            return

        slot.assigned_word = valid_words[0]
        self._refresh()
        self._update_selected_label()
        dir_he = "אופקי" if slot.direction == Direction.ACROSS else "אנכי"
        self.status_var.set(
            f"שובץ: '{valid_words[0]}' ב-{slot.clue_number} {dir_he} (מתוך {len(valid_words)} אפשרויות)"
        )

    def _suggest_words(self):
        if not self.selected_slot:
            messagebox.showwarning("שגיאה", "בחר הגדרה קודם.")
            return

        slot = self.selected_slot
        suggestions = self.solver.suggest_words_for_slot(
            slot.clue_number, slot.direction.name, max_results=20
        )

        self.suggestions_listbox.delete(0, tk.END)
        if suggestions:
            for word in suggestions:
                self.suggestions_listbox.insert(tk.END, word)
            self.status_var.set(f"נמצאו {len(suggestions)} הצעות (מתוך הדומיין המלא)")
        else:
            self.suggestions_listbox.insert(tk.END, "(אין מילים מתאימות)")
            self.status_var.set("לא נמצאו מילים מתאימות")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    arg_parser = argparse.ArgumentParser(description="פותר תשבצים קריפטיים - ממשק גרפי")
    arg_parser.add_argument("docx_path", nargs="?", default=None,
                            help="נתיב לקובץ ה-DOCX של התשבץ")
    arg_parser.add_argument("--wordbank", default="data/crossword_wordbank_he.txt",
                            help="נתיב לקובץ מאגר המילים")
    arg_parser.add_argument("--min-length", type=int, default=2,
                            help="אורך מילה מינימלי")
    args = arg_parser.parse_args()

    docx_path = args.docx_path
    if not docx_path:
        # Open file dialog if no path provided
        tmp_root = tk.Tk()
        tmp_root.withdraw()
        docx_path = filedialog.askopenfilename(
            title="בחר קובץ תשבץ",
            filetypes=[("Word Documents", "*.docx"), ("All Files", "*.*")]
        )
        tmp_root.destroy()
        if not docx_path:
            print("לא נבחר קובץ. יוצא.")
            sys.exit(0)

    try:
        raw_text = extract_text_from_docx(docx_path)
        result_matrix = parse_grid_to_matrix(raw_text)
        parsed_clues = parse_clues(raw_text)

        grid = Grid(result_matrix, min_word_length=args.min_length)
        link_clues_to_grid(grid, parsed_clues)

        solver = Solver(grid, args.wordbank)

        root = tk.Tk()
        app = CrosswordGUI(root, solver)
        root.mainloop()

    except Exception as e:
        messagebox.showerror("שגיאה", f"שגיאה בטעינת התשבץ:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
