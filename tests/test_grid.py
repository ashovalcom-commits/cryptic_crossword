from grid import Direction, Grid


def test_extract_slots_basic_across_and_down():
    layout = [
        "....",
        ".##.",
        "....",
        ".##.",
    ]
    grid = Grid(layout, min_word_length=3)

    across_slots = [s for s in grid.slots if s.direction == Direction.ACROSS]
    down_slots = [s for s in grid.slots if s.direction == Direction.DOWN]

    assert len(across_slots) == 2
    assert len(down_slots) == 2
    assert all(s.length == 4 for s in grid.slots)


def test_extract_slots_respects_min_word_length():
    # Row 0 has a run of length 2 ("..") which should be skipped when
    # min_word_length is 3, but row 1's run of length 4 should be kept.
    layout = [
        "..##",
        "....",
    ]
    grid = Grid(layout, min_word_length=3)

    across_slots = [s for s in grid.slots if s.direction == Direction.ACROSS]
    assert len(across_slots) == 1
    assert across_slots[0].length == 4
    assert across_slots[0].row == 1
    assert across_slots[0].col == 0


def test_extract_slots_skips_black_cells():
    layout = [
        "###",
        "###",
    ]
    grid = Grid(layout, min_word_length=2)

    assert grid.slots == []


def test_extract_slots_captures_clue_number():
    layout = [
        "1...",
        "....",
        "....",
    ]
    grid = Grid(layout, min_word_length=3)

    across_slot = next(s for s in grid.slots if s.direction == Direction.ACROSS and s.row == 0)
    down_slot = next(s for s in grid.slots if s.direction == Direction.DOWN and s.col == 0)

    assert across_slot.clue_number == "1"
    assert down_slot.clue_number == "1"


def test_extract_slots_no_clue_number_for_non_digit_cell():
    layout = [
        "....",
    ]
    grid = Grid(layout, min_word_length=3)

    assert len(grid.slots) == 1
    assert grid.slots[0].clue_number == ""


def test_calculate_intersections_basic_cross():
    # A simple plus-shaped intersection: one across slot and one down slot
    # crossing at a single cell.
    layout = [
        "..#",
        "...",
        "#.#",
    ]
    grid = Grid(layout, min_word_length=3)

    across_slot = next(s for s in grid.slots if s.direction == Direction.ACROSS)
    down_slot = next(s for s in grid.slots if s.direction == Direction.DOWN)

    assert across_slot.length == 3
    assert down_slot.length == 3
    assert len(across_slot.intersections) == 1
    assert len(down_slot.intersections) == 1

    a_index, other_slot, other_index = across_slot.intersections[0]
    assert other_slot is down_slot
    # The crossing cell is column 1 of the across slot, and row 1 of the down slot.
    assert a_index == 1
    assert other_index == 1

    d_index, other_slot2, other_index2 = down_slot.intersections[0]
    assert other_slot2 is across_slot
    assert d_index == 1
    assert other_index2 == 1


def test_calculate_intersections_none_when_slots_do_not_cross():
    layout = [
        "...",
        "###",
        "...",
    ]
    grid = Grid(layout, min_word_length=3)

    for slot in grid.slots:
        assert slot.intersections == []


def test_full_grid_slot_ids_are_sequential():
    layout = [
        "....",
        ".##.",
        "....",
        ".##.",
    ]
    grid = Grid(layout, min_word_length=3)

    ids = [s.id for s in grid.slots]
    assert ids == list(range(len(grid.slots)))
