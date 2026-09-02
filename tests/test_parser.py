from grid import Grid
from parser import link_clues_to_grid, parse_clues, parse_grid_to_matrix


def test_parse_grid_to_matrix_basic():
    raw_text = (
        ".|.|.|#|\n"
        ".|.|.|.|\n"
        "---BOARD_END---\n"
    )

    matrix = parse_grid_to_matrix(raw_text, cols=4)

    assert matrix == [
        [".", ".", ".", "#"],
        [".", ".", ".", "."],
    ]


def test_parse_grid_to_matrix_keeps_clue_numbers():
    raw_text = (
        "1|2|#|\n"
        ".|.|.|\n"
        "---BOARD_END---\n"
    )

    matrix = parse_grid_to_matrix(raw_text, cols=3)

    assert matrix == [
        ["1", "2", "#"],
        [".", ".", "."],
    ]


def test_parse_grid_to_matrix_expands_merged_black_cells():
    # "##" in a single docx cell represents a merged span of two black cells.
    raw_text = (
        "##|.|.|\n"
        ".|.|.|\n"
        "---BOARD_END---\n"
    )

    matrix = parse_grid_to_matrix(raw_text, cols=3)

    assert matrix == [
        ["#", "#", "."],
        [".", ".", "."],
    ]


def test_parse_grid_to_matrix_drops_incomplete_trailing_row():
    raw_text = (
        ".|.|.|\n"
        ".|.|\n"  # incomplete row, should be dropped
        "---BOARD_END---\n"
    )

    matrix = parse_grid_to_matrix(raw_text, cols=3)

    assert matrix == [[".", ".", "."]]


def test_parse_clues_splits_across_and_down():
    raw_text = (
        "---BOARD_END---\n"
        "אופקי:\n"
        "1. הגדרה ראשונה (4)\n"
        "אנכי:\n"
        "2. הגדרה שנייה (3)\n"
    )

    clues = parse_clues(raw_text)

    assert set(clues["ACROSS"].keys()) == {"1"}
    assert set(clues["DOWN"].keys()) == {"2"}
    assert clues["ACROSS"]["1"]["lengths"] == "4"
    assert clues["DOWN"]["2"]["lengths"] == "3"


def test_parse_clues_handles_split_clue_number():
    # Clues like "23+8 אופקי." denote a definition shared across two slots.
    raw_text = (
        "---BOARD_END---\n"
        "אופקי:\n"
        "23+8 אופקי. הגדרה מפוצלת (3,4)\n"
        "אנכי:\n"
    )

    clues = parse_clues(raw_text)

    assert "23+8 אופקי" in clues["ACROSS"]
    assert clues["ACROSS"]["23+8 אופקי"]["lengths"] == "3,4"


def test_parse_clues_moves_length_pattern_to_end_of_text():
    raw_text = (
        "---BOARD_END---\n"
        "אופקי:\n"
        "5. מילה עם (3) אותיות באמצע המשפט\n"
        "אנכי:\n"
    )

    clues = parse_clues(raw_text)

    clue = clues["ACROSS"]["5"]
    assert clue["lengths"] == "3"
    assert clue["text"].endswith("(3)")
    assert "מילה עם" in clue["text"]


def test_parse_clues_multiple_clues_are_split_correctly():
    raw_text = (
        "---BOARD_END---\n"
        "אופקי:\n"
        "1. הגדרה אחת (3)\n"
        "2. הגדרה שתיים (4)\n"
        "אנכי:\n"
    )

    clues = parse_clues(raw_text)

    assert clues["ACROSS"]["1"]["text"] == "הגדרה אחת (3)"
    assert clues["ACROSS"]["2"]["text"] == "הגדרה שתיים (4)"


def test_parse_clues_without_lengths_pattern():
    raw_text = (
        "---BOARD_END---\n"
        "אופקי:\n"
        "7. הגדרה בלי אורך בסוגריים\n"
        "אנכי:\n"
    )

    clues = parse_clues(raw_text)

    assert clues["ACROSS"]["7"]["lengths"] == ""


def test_parse_clues_without_down_section():
    raw_text = (
        "---BOARD_END---\n"
        "9. הגדרה יחידה (5)\n"
    )

    clues = parse_clues(raw_text)

    assert clues["ACROSS"]["9"]["lengths"] == "5"
    assert clues["DOWN"] == {}


def test_link_clues_to_grid_matches_plain_clue_number():
    layout = ["1...", "....", "....", "...."]
    grid = Grid(layout, min_word_length=3)

    raw_text = (
        "---BOARD_END---\n"
        "אופקי:\n"
        "1. הגדרה אופקית (4)\n"
        "אנכי:\n"
        "1. הגדרה אנכית (4)\n"
    )
    clues = parse_clues(raw_text)

    link_clues_to_grid(grid, clues)

    slots_with_clue_1 = [s for s in grid.slots if s.clue_number == "1"]
    assert len(slots_with_clue_1) == 2
    assert all(s.clue_text for s in slots_with_clue_1)


def test_link_clues_to_grid_matches_split_clue_number():
    layout = ["1..."]
    grid = Grid(layout, min_word_length=3)
    grid.slots[0].clue_number = "23"

    raw_text = (
        "---BOARD_END---\n"
        "אופקי:\n"
        "23+8 אופקי. הגדרה מפוצלת (3,4)\n"
        "אנכי:\n"
    )
    clues = parse_clues(raw_text)

    link_clues_to_grid(grid, clues)

    assert grid.slots[0].clue_text == "הגדרה מפוצלת (3,4)"


def test_link_clues_to_grid_no_match_leaves_clue_text_empty():
    layout = ["...."]
    grid = Grid(layout, min_word_length=3)
    grid.slots[0].clue_number = "99"

    raw_text = (
        "---BOARD_END---\n"
        "אופקי:\n"
        "1. הגדרה לא רלוונטית (4)\n"
        "אנכי:\n"
    )
    clues = parse_clues(raw_text)

    link_clues_to_grid(grid, clues)

    assert grid.slots[0].clue_text == ""
