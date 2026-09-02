import requests
import gzip
import os
import re

DUMPS_URL = "https://dumps.wikimedia.org/hewiki/latest/hewiki-latest-all-titles-in-ns0.gz"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "crossword_wordbank_he.txt")

def build_crossword_bank():
    print("מוריד את קובץ הכותרות מויקימדיה (עשוי לקחת כמה שניות)...")
    headers = {
        'User-Agent': 'CrosswordBuilder/1.0 (Personal Project)'
    }
    response = requests.get(DUMPS_URL, headers=headers)
    response.raise_for_status()
    
    raw_data = gzip.decompress(response.content).decode('utf-8')
    titles = raw_data.split('\n')
    
    # word (מחובר) -> תבנית חלוקה למילים כמחרוזת ("4,6"), או "" אם המילה
    # הגיעה במקור כטוקן בודד (ללא רווחים) ולכן לא ידועה תבנית חלוקה שלה.
    # אם אותה מילה מחוברת מגיעה מכותרות שונות עם תבניות סתירה, שומרים "" (לא ידוע),
    # כדי לא להטעות בהמשך את מנוע ההצעות.
    clean_words: dict = {}
    hebrew_only_pattern = re.compile(r'^[א-ת]+$')
    
    # טבלת המרה מאותיות סופיות לרגילות
    final_to_regular = str.maketrans('ךםןףץ', 'כמנפצ')
    
    def normalize_part(part: str) -> str:
        part = re.sub(r'[\-׳״\'"]', '', part)
        return part.translate(final_to_regular)
    
    print(f"עובר על {len(titles):,} כותרות...")
    
    for title in titles:
        if not title or '(' in title or any(char.isdigit() for char in title):
            continue
        
        # מפרידים למילים לפי רווחים/קו-תחתי (מציין רווח בכותרות ויקיפדיה),
        # לפני שמנרמלים כל מילה בנפרד. כך אפשר לשמור את אורך כל מילה כפי שהיא
        # מופיעה במקור, ולא רק את סך האותיות הכולל אחרי המחיקה.
        raw_parts = [p for p in re.split(r'[_ ]+', title) if p]
        parts = [normalize_part(p) for p in raw_parts]
        
        if not parts or not all(hebrew_only_pattern.match(p) for p in parts):
            continue
        
        joined = ''.join(parts)
        if not (3 <= len(joined) <= 15):
            continue
        
        pattern = ','.join(str(len(p)) for p in parts) if len(parts) > 1 else ''
        
        if joined in clean_words and clean_words[joined] != pattern:
            # תבניות מנוגדות עבור אותה מילה מחוברת - מסמנים כלא ידוע
            clean_words[joined] = ''
        else:
            clean_words[joined] = pattern
            
    print(f"נמצאו {len(clean_words):,} ערכים תקינים. שומר לקובץ...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for word in sorted(clean_words):
            pattern = clean_words[word]
            if pattern:
                f.write(f"{word}\t{pattern}\n")
            else:
                f.write(word + '\n')
            
    print(f"הקובץ {OUTPUT_FILE} מוכן לעבודה!")

if __name__ == "__main__":
    build_crossword_bank()