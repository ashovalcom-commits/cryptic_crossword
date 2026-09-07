import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from hebrew_utils import process_title, write_wordbank

# נתיב לקובץ המילון המקומי (יש לעדכן לנתיב בו שמרת את המילון)
# הפורמט המצופה: קובץ טקסט שבו כל שורה מכילה מילה ארמית (או מילה,פסיק,תרגום)
DICTIONARY_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sources", "aramaic_hebrew_dict.txt")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sources", "dictionary_arc.txt")

def fetch_and_convert_dictionary():
    print(f"קורא את מאגר המילים מתוך המילון: {DICTIONARY_FILE}...")
    
    if not os.path.exists(DICTIONARY_FILE):
        print(f"שגיאה: הקובץ {DICTIONARY_FILE} לא נמצא. אנא ודא שהקובץ קיים בנתיב.")
        return {}

    with open(DICTIONARY_FILE, 'r', encoding='utf-8') as f:
        lines = f.read().splitlines()
        
    print(f"עובר על {len(lines):,} שורות מהמילון...")

    words: dict = {}
    for line in lines:
        # ניקוי השורה: אם הקובץ מכיל גם תרגום מופרד בפסיק או טאב, ניקח רק את החלק הראשון (המילה)
        # אם זה רק רשימת מילים, הפעולה הזו לא תפריע.
        raw_word = line.split(',')[0].split('\t')[0].strip()
        
        if not raw_word:
            continue
            
        result = process_title(raw_word)
        if result is None:
            continue
            
        word, pattern = result
        if word in words and words[word] != pattern:
            words[word] = ''
        else:
            words[word] = pattern

    print(f"נמצאו {len(words):,} ערכים תקינים מתוך המילון.")
    return words

def build_crossword_bank():
    words = fetch_and_convert_dictionary()
    if words:
        write_wordbank(words, OUTPUT_FILE)
        print(f"הקובץ {OUTPUT_FILE} מוכן לעבודה!")
    else:
        print("לא נוצר קובץ פלט מכיוון שלא נמצאו מילים תקינות.")

if __name__ == "__main__":
    build_crossword_bank()


# import os
# import sys
# import gzip
# import requests

# sys.path.insert(0, os.path.dirname(__file__))
# from hebrew_utils import process_title, write_wordbank

# DUMPS_URL = "https://dumps.wikimedia.org/arcwiki/latest/arcwiki-latest-all-titles-in-ns0.gz"
# OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sources", "wikipedia_arc.txt")

# # טבלת המרה מאלפבית סורי לאלפבית עברי
# SYRIAC_TO_HEBREW = str.maketrans(
#     'ܐܒܓܕܗܘܙܚܛܝܟܠܡܢܣܥܦܨܩܪܫܬ',
#     'אבגדהוזחטיכלמנסעפצקרשת'
# )

# def fetch_and_convert_arcwiki():
#     print("מוריד את קובץ הכותרות מוויקיפדיה הארמית...")
#     headers = {'User-Agent': 'CrosswordBuilder/1.0 (Personal Project)'}
#     response = requests.get(DUMPS_URL, headers=headers)
#     response.raise_for_status()

#     raw_data = gzip.decompress(response.content).decode('utf-8')
#     titles = raw_data.split('\n')
#     print(f"עובר על {len(titles):,} כותרות וממיר מכתב סורי לעברי...")

#     words: dict = {}
#     for title in titles:
#         # המרת הכתב לפני הסינון
#         hebrew_title = title.translate(SYRIAC_TO_HEBREW)
        
#         result = process_title(hebrew_title)
#         if result is None:
#             continue
            
#         word, pattern = result
#         if word in words and words[word] != pattern:
#             words[word] = ''
#         else:
#             words[word] = pattern

#     print(f"נמצאו {len(words):,} ערכים תקינים מתוך ויקיפדיה הארמית.")
#     return words

# def build_crossword_bank():
#     words = fetch_and_convert_arcwiki()
#     write_wordbank(words, OUTPUT_FILE)
#     print(f"הקובץ {OUTPUT_FILE} מוכן לעבודה!")

# if __name__ == "__main__":
#     build_crossword_bank()