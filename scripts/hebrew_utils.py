"""
כלים משותפים לסקריפטים שבונים את מאגר המילים: ניקוי כותרות/מילים גולמיות
לפורמט האחיד של המאגר (מילה + תבנית חלוקה למילים כשזו ידועה), הורדה ופענוח
של קובצי דאמפ דחוסים (gzip) מוויקימדיה, מיזוג מאגרים ושמירה לקובץ.
"""

import gzip
import os
import re

import requests

# טבלת המרה מאותיות סופיות לרגילות - כדי שאותה אות תיוצג תמיד באותו אופן בלוח
# (תא בלוח לא מבחין בין "ם" ל"מ" לפי מיקום המילה).
FINAL_TO_REGULAR = str.maketrans('ךםןףץ', 'כמנפצ')

HEBREW_ONLY_PATTERN = re.compile(r'^[א-ת]+$')


def normalize_part(part: str) -> str:
    """מנקה מקף/גרש/גרשיים מחלק מילה בודד וממיר אותיות סופיות לרגילות."""
    part = re.sub(r'[\-׳״\'"]', '', part)
    return part.translate(FINAL_TO_REGULAR)


def process_title(title: str, min_len: int = 3, max_len: int = 15):
    """
    מנקה כותרת/מילה גולמית אחת ומחזירה (מילה_מחוברת, תבנית) או None אם הערך לא תקין.

    התבנית היא מחרוזת אורכי החלקים מופרדת בפסיקים (למשל "4,6") כאשר הכותרת
    הגיעה עם כמה מילים מופרדות ברווח/קו-תחתי, או "" כאשר הכותרת הגיעה כטוקן
    בודד (חלוקה לא ידועה).
    """
    if not title or '(' in title or any(ch.isdigit() for ch in title):
        return None

    raw_parts = [p for p in re.split(r'[_ ]+', title) if p]
    parts = [normalize_part(p) for p in raw_parts]

    if not parts or not all(HEBREW_ONLY_PATTERN.match(p) for p in parts):
        return None

    joined = ''.join(parts)
    if not (min_len <= len(joined) <= max_len):
        return None

    pattern = ','.join(str(len(p)) for p in parts) if len(parts) > 1 else ''
    return joined, pattern


def merge_words(target: dict, source: dict) -> None:
    """
    ממזג מאגר words (word -> pattern) לתוך target, במקום.
    אם מילה כבר קיימת ב-target עם תבנית שונה - מסמנים כלא ידוע ("), כדי לא
    להטעות בהמשך את מנוע ההצעות עם תבנית סותרת ממקור אחר.
    """
    for word, pattern in source.items():
        if word in target and target[word] != pattern:
            target[word] = ''
        else:
            target[word] = pattern


def fetch_titles_from_dump(url: str, source_label: str) -> dict:
    """מוריד דאמפ כותרות דחוס (gzip) מוויקימדיה ומחזיר מאגר words (word -> pattern)."""
    print(f"מוריד את קובץ הכותרות מ-{source_label} (עשוי לקחת כמה שניות)...")
    headers = {'User-Agent': 'CrosswordBuilder/1.0 (Personal Project)'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    raw_data = gzip.decompress(response.content).decode('utf-8')
    titles = raw_data.split('\n')
    print(f"עובר על {len(titles):,} כותרות...")

    words: dict = {}
    for title in titles:
        result = process_title(title)
        if result is None:
            continue
        word, pattern = result
        if word in words and words[word] != pattern:
            words[word] = ''
        else:
            words[word] = pattern

    print(f"נמצאו {len(words):,} ערכים תקינים מ-{source_label}.")
    return words


def fetch_hspell_base_words(url: str, source_label: str) -> dict:
    """
    מוריד את מילון היסוד (ללא צירופי תחיליות) של Hspell בפורמט Hunspell
    (קובץ .dic) ומחזיר מאגר words (word -> ""). כל ערך במילון זה הוא מילה
    בודדת (ללא רווחים), ולכן תבנית החלוקה תמיד לא ידועה ("").
    """
    print(f"מוריד את מילון hspell (בסיס, ללא צירופי תחיליות) מ-{source_label}...")
    headers = {'User-Agent': 'CrosswordBuilder/1.0 (Personal Project)'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    lines = response.content.decode('utf-8').split('\n')
    print(f"עובר על {len(lines):,} שורות...")

    words: dict = {}
    for line in lines[1:]:  # השורה הראשונה היא מספר הערכים במילון, לא מילה
        line = line.strip()
        if not line:
            continue
        word = normalize_part(line.split('/', 1)[0])
        if not HEBREW_ONLY_PATTERN.match(word):
            continue
        if not (3 <= len(word) <= 15):
            continue
        words[word] = ''

    print(f"נמצאו {len(words):,} ערכים תקינים מ-{source_label}.")
    return words


def write_wordbank(words: dict, path: str) -> None:
    """שומר מאגר words (word -> pattern) לקובץ בפורמט הסטנדרטי של המאגר."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        for word in sorted(words):
            pattern = words[word]
            if pattern:
                f.write(f"{word}\t{pattern}\n")
            else:
                f.write(word + '\n')
