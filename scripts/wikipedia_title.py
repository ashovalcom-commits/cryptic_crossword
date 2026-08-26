import requests
import gzip
import re

DUMPS_URL = "https://dumps.wikimedia.org/hewiki/latest/hewiki-latest-all-titles-in-ns0.gz"
OUTPUT_FILE = "crossword_wordbank_he.txt"

def build_crossword_bank():
    print("מוריד את קובץ הכותרות מויקימדיה (עשוי לקחת כמה שניות)...")
    headers = {
        'User-Agent': 'CrosswordBuilder/1.0 (Personal Project)'
    }
    response = requests.get(DUMPS_URL, headers=headers)
    response.raise_for_status()
    
    raw_data = gzip.decompress(response.content).decode('utf-8')
    titles = raw_data.split('\n')
    
    clean_words = set()
    hebrew_only_pattern = re.compile(r'^[א-ת]+$')
    
    # טבלת המרה מאותיות סופיות לרגילות
    final_to_regular = str.maketrans('ךםןףץ', 'כמנפצ')
    
    print(f"עובר על {len(titles):,} כותרות...")
    
    for title in titles:
        if not title or '(' in title or any(char.isdigit() for char in title):
            continue
            
        normalized = re.sub(r'[_ \-׳״\'"]', '', title)
        
        # המרת האותיות הסופיות
        normalized = normalized.translate(final_to_regular)
        
        if 3 <= len(normalized) <= 15 and hebrew_only_pattern.match(normalized):
            clean_words.add(normalized)
            
    print(f"נמצאו {len(clean_words):,} ערכים תקינים. שומר לקובץ...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for word in sorted(clean_words):
            f.write(word + '\n')
            
    print(f"הקובץ {OUTPUT_FILE} מוכן לעבודה!")

if __name__ == "__main__":
    build_crossword_bank()