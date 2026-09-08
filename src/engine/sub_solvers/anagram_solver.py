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
        
        # בניית ביטוי רגולרי לחיפוש והסרת אינדיקטורים שלמים (כדי לא לחתוך חלקי מילים)
        # לדוגמה: '\b(מעורבב|אחרת|התבלבל)\b'
        indicators_pattern = r'\b(' + '|'.join(self.indicators) + r')\b'
        self.indicators_regex = re.compile(indicators_pattern)
        
        # טבלת המרה לאותיות סופיות בעברית
        self.final_letters_map = str.maketrans("םןףץך", "מנפצכ")

    def is_valid_match(self, candidate: str, wordplay_text: str, target_length: int) -> bool:
        # 1. פסילה מהירה (Early exit): אם אורך המועמד שגוי
        if len(candidate) != target_length:
            return False
            
        # 2. ניקוי מילות ההוראה (אינדיקטורים) מהטקסט של משחק המילים
        clean_wordplay = self._remove_indicators(wordplay_text)
        
        # הסרת רווחים (כיוון שאנגרמה מתייחסת לרצף האותיות הכללי)
        clean_wordplay = clean_wordplay.replace(" ", "")
        
        # 3. פסילה מהירה נוספת: אם אחרי הניקוי מספר האותיות לא תואם לאורך המבוקש
        if len(clean_wordplay) != target_length:
            return False
            
        # 4. נרמול אותיות סופיות עבור המועמד ועבור אותיות משחק המילים
        candidate_normalized = self._normalize_hebrew(candidate)
        wordplay_normalized = self._normalize_hebrew(clean_wordplay)
        
        # 5. בדיקה מתמטית: האם תדירות האותיות זהה לחלוטין
        return Counter(candidate_normalized) == Counter(wordplay_normalized)
        
    def _remove_indicators(self, text: str) -> str:
        """מסיר את מילות ההוראה ממשפט משחק המילים"""
        # מחליף את האינדיקטורים במחרוזת ריקה
        clean_text = self.indicators_regex.sub('', text)
        # מנקה רווחים כפולים שנוצרו
        return " ".join(clean_text.split())
        
    def _normalize_hebrew(self, text: str) -> str:
        """ממיר אותיות סופיות לאותיות רגילות"""
        return text.translate(self.final_letters_map)