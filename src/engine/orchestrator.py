from typing import List
from engine.sub_solvers.base_solver import BaseWordplaySolver
from engine.splitters import ParsedClue, generate_splits


class CrypticEngine:
    def __init__(self, solvers: List[BaseWordplaySolver], semantic_api):
        self.solvers = solvers
        self.semantic_api = semantic_api # יכול להיות קליינט של Claude או מאגר מקומי

    def solve(self, clue: ParsedClue) -> List[str]:
        valid_answers = []
        splits = generate_splits(clue.original_text)
        
        for split in splits:
            # שלב א': הבאת מועמדים מהחלק שאנחנו מניחים שהוא ההגדרה הישירה
            # כאן קוראים ל-API הסמנטי (או משתמשים במאגר לוקאלי)
            candidates = self.semantic_api.get_synonyms(
                term=split.definition_part, 
                length_limit=clue.length
            )
            
            # שלב ב': הרצת המועמדים דרך מנועי משחקי המילים השונים
            for candidate in candidates:
                for solver in self.solvers:
                    if solver.is_valid_match(candidate, split.wordplay_part, clue.length):
                        valid_answers.append(candidate)
                        
        return list(set(valid_answers)) # החזרת תשובות ייחודיות