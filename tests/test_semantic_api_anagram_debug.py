import os
from pathlib import Path

from engine.semantic_api import ClaudeSemanticAPI
from engine.splitters import ParsedClue, generate_splits
from engine.sub_solvers.anagram_solver import AnagramSolver


LOG_PATH = Path(__file__).resolve().parent / "semantic_anagram_debug_log.txt"


class LocalSemanticFallback:
    """Fallback for local debugging when ANTHROPIC_API_KEY is not configured."""

    def get_synonyms(self, term: str, length_limit: int):
        term = (term or "").strip()
        # Keep the same interface as ClaudeSemanticAPI.get_synonyms.
        # These values are hand-picked to exercise the actual clue flow from
        # algo_logics/anagram_logics.txt: definition "זמר" -> semantic word "שירה".
        candidates_map = {
            "זמר": ["שירה", "זמר", "מרז"],
            "הר שי אחר": ["הרשי", "שיר"],
        }
        suggested = candidates_map.get(term, [term]) if term else [term]
        return [w for w in suggested if len(w) == length_limit and w.isalpha()]


def build_semantic_api():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if api_key:
        try:
            api = ClaudeSemanticAPI(api_key=api_key)
            print(f"Using real ClaudeSemanticAPI with ANTHROPIC_API_KEY present.")
            return api
        except Exception as exc:
            print(f"ClaudeSemanticAPI init failed: {exc}. Falling back to local stub.")

    print("ANTHROPIC_API_KEY is missing; using LocalSemanticFallback for debugging.")
    return LocalSemanticFallback()


def test_debug_semantic_api_anagram_flow():
    solver = AnagramSolver()
    semantic_api = build_semantic_api()
    clue = ParsedClue(original_text="הר שי אחר זמר", length=4)

    lines = []
    lines.append("=== Semantic + Anagram debug ===")
    lines.append(f"clue: {clue.original_text}")
    lines.append(f"target_length: {clue.length}")
    lines.append("")

    splits = generate_splits(clue.original_text)
    lines.append(f"generated splits: {len(splits)}")
    for i, split in enumerate(splits, start=1):
        lines.append("-" * 60)
        lines.append(f"Split #{i}: definition='{split.definition_part}' | wordplay='{split.wordplay_part}'")

        candidates = semantic_api.get_synonyms(split.definition_part, clue.length)
        lines.append(f"semantic candidates for definition: {candidates}")

        if not candidates:
            lines.append("No candidates returned by semantic API for this definition.")
            continue

        for candidate in candidates:
            result = solver.is_valid_match(candidate, split.wordplay_part, clue.length)
            lines.append(
                f"  candidate={candidate!r}, len={len(candidate)}, "
                f"wordplay_part={split.wordplay_part!r}, solver_result={result}"
            )

            if result:
                lines.append(f"  ACCEPTED candidate: {candidate}")
                break

    LOG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nDebug log written to: {LOG_PATH}")

    assert LOG_PATH.exists()
    assert any("ACCEPTED candidate" in line for line in lines)
