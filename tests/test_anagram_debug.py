from collections import Counter

from engine.sub_solvers.anagram_solver import AnagramSolver


def test_debug_anagram_solver_for_simple_clue():
    # Example straight from algo_logics/anagram_logics.txt:
    # clue "הר שי אחר זמר", target_length=4, indicator "אחר" removed,
    # partition ["הרשי", "זמר"] -> fodder="הרשי", definition="זמר".
    solver = AnagramSolver()

    clue = "הר שי אחר זמר"
    target_length = 4
    wordplay = "הר שי אחר"  # everything except the definition_part "זמר"
    candidates = ["שירה", "זמר", "הרשי", "מזרח"]

    print("=" * 80)
    print(f"Clue: {clue}")
    print(f"Target length: {target_length}")
    print("=" * 80)
    print("\n1) Split clue into definition and wordplay")
    print(f"definition_part = 'זמר'")
    print(f"wordplay_part (fodder source) = '{wordplay}'")

    fodder = solver._build_fodder(wordplay)
    print(f"\n2) Fodder after removing indicators and joining letters: {fodder!r} (len={len(fodder)})")

    print("\n3) Check each candidate one by one")
    for candidate in candidates:
        normalized = solver._normalize_hebrew("".join(candidate.split()))
        match_counter = Counter(normalized)
        final_result = solver.is_valid_match(candidate, wordplay, target_length)

        print("\n---")
        print(f"candidate: {candidate!r}")
        print(f"normalized candidate: {normalized!r}")
        print(f"letter counts: {dict(match_counter)}")
        print(f"solver.is_valid_match(...) -> {final_result}")

    print("\n4) Final verdict for the correct answer")
    answer = "שירה"
    final_verdict = solver.is_valid_match(answer, wordplay, target_length)
    print(f"candidate = {answer!r}")
    print(f"final_verdict = {final_verdict}")

    assert final_verdict is True
