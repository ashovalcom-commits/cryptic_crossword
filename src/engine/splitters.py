from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ParsedClue:
    original_text: str
    length: int
    
@dataclass
class ClueSplit:
    definition_part: str
    wordplay_part: str
    
def generate_splits(clue: str) -> List[ClueSplit]:
    """מייצר את כל נקודות החיתוך האפשריות של ההגדרה"""
    words = clue.split()
    splits = []
    # רץ על כל נקודות החיתוך האפשריות (מתעלם ממילה בודדת)
    for i in range(1, len(words)):
        part_a = " ".join(words[:i])
        part_b = " ".join(words[i:])
        # מוסיף את שתי האופציות (פעם ימין הגדרה, ופעם שמאל)
        splits.append(ClueSplit(definition_part=part_a, wordplay_part=part_b))
        splits.append(ClueSplit(definition_part=part_b, wordplay_part=part_a))
    return splits