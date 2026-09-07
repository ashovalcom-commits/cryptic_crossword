import os
import sys
import requests

sys.path.insert(0, os.path.dirname(__file__))
from hebrew_utils import process_title, write_wordbank

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sources", "wiktionary_aramaic.txt")

# הקטגוריות בוויקימילון שמכילות מילים וביטויים בארמית שרלוונטיים לעברית
CATEGORIES = [
    "קטגוריה:מילים_שאולות_מהשפה_הארמית",
    "קטגוריה:ניבים,_ביטויים_ופתגמים_בארמית",
    "קטגוריה:ראשי_תיבות_בארמית"
]

def fetch_wiktionary_category(category):
    url = "https://he.wiktionary.org/w/api.php"
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": category,
        "cmlimit": "max",
        "format": "json"
    }
    
    words = []
    # מגדירים User-Agent מנומס כדי לא להיחסם
    headers = {'User-Agent': 'CrosswordBuilder/1.0 (Personal Project)'}
    
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        data = response.json()
        members = data.get("query", {}).get("categorymembers", [])
        for member in members:
            title = member.get("title", "")
            # מסננים דפי קטגוריה או תבניות (לוקחים רק ערכים אמיתיים)
            if not title.startswith("קטגוריה:") and not title.startswith("תבנית:"):
                words.append(title)
    return words

def fetch_and_convert_wiktionary():
    print("מתחבר ל-API של ויקימילון העברי...")
    
    all_words = set()
    for cat in CATEGORIES:
        print(f"מושך נתונים מהקטגוריה: {cat.replace('_', ' ')}...")
        cat_words = fetch_wiktionary_category(cat)
        all_words.update(cat_words)
        
    print(f"בסך הכל נמשכו {len(all_words)} ביטויים ומילים בארמית.")

    words_dict: dict = {}
    for raw_word in all_words:
        result = process_title(raw_word)
        if result is None:
            continue
            
        word, pattern = result
        if word in words_dict and words_dict[word] != pattern:
            words_dict[word] = ''
        else:
            words_dict[word] = pattern

    print(f"נמצאו {len(words_dict):,} ערכים תקינים שהומרו בהצלחה.")
    return words_dict

def build_crossword_bank():
    words = fetch_and_convert_wiktionary()
    if words:
        write_wordbank(words, OUTPUT_FILE)
        print(f"הקובץ {OUTPUT_FILE} מוכן לעבודה בתיקיית data/sources!")
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