from collections import Counter
from typing import List
import re
from .base_solver import BaseWordplaySolver

class AnagramSolver(BaseWordplaySolver):
    def __init__(self, indicators: List[str] = None):
        # רשימת ברירת מחדל של מילות הוראה לאנגרמה בתשבצי היגיון עבריים
        self.indicators = indicators or [
            "מעורבב", "מעורבבים", "התבלבל", "התבלבלה", 
            "אחרת", "סדר חדש", "מבולבל", "בשינוי", 
            "הפוך", "לסדר", "שוב", "אחר", "שונה", 
        ]
        
        # בניית ביטוי רגולרי לחיפוש והסרת אינדיקטורים שלמים
        indicators_pattern = r'\b(' + '|'.join(self.indicators) + r')\b'
        self.indicators_regex = re.compile(indicators_pattern)
        
        # טבלת המרה לאותיות סופיות בעברית
        self.final_letters_map = str.maketrans("םןףץך", "מנפצכ")

    def is_valid_match(self, candidate: str, wordplay_text: str, target_length: int) -> bool:
        """
        wordplay_text הוא ה-fodder של האנגרמה. מסירים ממנו מילות הוראה, מנרמלים
        אותיות סופיות ומאחדים לרצף אותיות רציף. המועמד תקף רק אם יש לו בדיוק
        את אותו אורך ואת אותה קבוצת אותיות (אנגרמה) כמו ה-fodder.
        """
        if not candidate:
            return False

        fodder = self._build_fodder(wordplay_text)
        if len(fodder) != target_length:
            return False

        candidate_letters = self._normalize_hebrew("".join(candidate.split()))
        if len(candidate_letters) != target_length:
            return False

        return Counter(fodder) == Counter(candidate_letters)

    def _build_fodder(self, wordplay_text: str) -> str:
        """מסיר מילות הוראה, מנרמל אותיות סופיות ומאחד למחרוזת אותיות רציפה"""
        clean_text = self._remove_indicators(wordplay_text)
        normalized = self._normalize_hebrew(clean_text)
        return "".join(normalized.split())

    def _remove_indicators(self, text: str) -> str:
        """מסיר את מילות ההוראה ממשפט משחק המילים"""
        clean_text = self.indicators_regex.sub('', text)
        return " ".join(clean_text.split())
        
    def _normalize_hebrew(self, text: str) -> str:
        """ממיר אותיות סופיות לאותיות רגילות"""
        return text.translate(self.final_letters_map)