import os
from typing import List
from anthropic import Anthropic, AuthenticationError

class ClaudeSemanticAPI:
    def __init__(self, api_key: str = None):
        # מתחבר אוטומטית אם יש משתנה סביבה ANTHROPIC_API_KEY, אחרת מקבל מפתח כפרמטר
        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ValueError(
                "לא סופק מפתח Anthropic API. הגדר משתנה סביבה ANTHROPIC_API_KEY "
                "או העבר api_key בעת יצירת ClaudeSemanticAPI."
            )
        self.client = Anthropic(api_key=resolved_key)
        # claude-3-5-sonnet-20240620 הוצא משימוש (404). שימוש במודל הנוכחי claude-sonnet-5.
        self.model = "claude-sonnet-5"

    def get_synonyms(self, term: str, length_limit: int) -> List[str]:
        # הנדסת פרומפט (Prompt Engineering) מדויקת עבור משימת חילוץ מילים
        prompt = (
            f"אתה מומחה לשפה העברית ולתשבצי היגיון.\n"
            f"ספק רשימה של עד 30 מילים נרדפות, הגדרות, או אסוציאציות ישירות למונח: '{term}'.\n"
            f"אילוץ קריטי: כל מילה ברשימה חייבת להיות מורכבת מבדיוק {length_limit} אותיות (ללא רווחים).\n"
            f"החזר אך ורק את המילים מופרדות בפסיקים, ללא שום טקסט מקדים, ללא מספור וללא הסברים."
        )
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                #temperature=0.7, # מאפשר גמישות מסוימת באסוציאציות
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # חילוץ הטקסט הגולמי מהתשובה של קלוד
            # במודלים עם adaptive thinking, content עשוי לכלול גם ThinkingBlock,
            # לכן מחפשים באופן מפורש את בלוק הטקסט (type == "text").
            raw_text = next(
                (block.text for block in response.content if block.type == "text"),
                ""
            )
            
            # פיצול לפי פסיק וניקוי רווחים מיותרים
            words = [word.strip() for word in raw_text.split(',')]
            
            # פילטר בטיחות: למרות שהורנו לקלוד להחזיר אורך מסוים, LLMs טועים לעיתים בספירת תווים.
            # כאן פייתון מבצע וידוא אכזרי שאכן המילים באורך המדויק.
            valid_words = [w for w in words if len(w) == length_limit and w.isalpha()]
            
            return valid_words

        except AuthenticationError as e:
            print(
                "Anthropic authentication failed (401). "
                "בדוק שמשתנה הסביבה ANTHROPIC_API_KEY מכיל מפתח תקין, פעיל ולא פג תוקף: "
                f"{e}"
            )
            return []
        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return []