from abc import ABC, abstractmethod

class BaseWordplaySolver(ABC):
    """
    מחלקת בסיס אבסטרקטית לכל מנועי משחקי המילים.
    כל סולבר חדש (אנגרמות, מילים חבויות וכו') חייב לרשת ממנה ולממש את is_valid_match.
    """
    @abstractmethod
    def is_valid_match(self, candidate: str, wordplay_text: str, target_length: int) -> bool:
        """
        מקבל מועמד (שיצא משלב ההגדרה), את הטקסט של משחק המילים, ואת אורך התשובה.
        מחזיר True אם המועמד מקיים את חוקיות משחק המילים, אחרת False.
        """
        pass