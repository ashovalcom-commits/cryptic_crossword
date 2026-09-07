"""
מריץ את כל סקריפטי המקורות (ויקיפדיה, ויקימילון, Hspell, ומילים ארמיות מויקימילון) וממזג את התוצאות
שלהם למאגר מילים אחד: data/crossword_wordbank_he.txt.

כל מקור נשמר גם בנפרד תחת data/sources/, כך שאפשר להריץ מקור בודד
(למשל scripts/wikipedia_title.py) בלי לגעת במאגר הכולל.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from hebrew_utils import merge_words, write_wordbank
from wikipedia_title import build_crossword_bank as build_wikipedia
from wiktionary_title import build_crossword_bank as build_wiktionary
from hspell_wordlist import build_crossword_bank as build_hspell
from arcwiki_title import build_crossword_bank as build_arcwiki

SOURCES_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sources")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "crossword_wordbank_he.txt")

SOURCE_FILES = [
    "wikipedia_he.txt",
    "wiktionary_he.txt",
    "hspell_he.txt",
    "wiktionary_aramaic.txt",
]


def load_wordbank(path: str) -> dict:
    words: dict = {}
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            if not line:
                continue
            if '\t' in line:
                word, pattern = line.split('\t', 1)
            else:
                word, pattern = line, ''
            words[word] = pattern
    return words


def build_all_sources():
    print("=== מקור 1/4: ויקיפדיה ===")
    build_wikipedia()
    print("\n=== מקור 2/4: ויקימילון ===")
    build_wiktionary()
    print("\n=== מקור 3/4: Hspell ===")
    build_hspell()
    print("\n=== מקור 4/4: ויקימילון (ארמית) ===")
    build_arcwiki()


def merge_sources():
    merged: dict = {}
    for filename in SOURCE_FILES:
        path = os.path.join(SOURCES_DIR, filename)
        if not os.path.exists(path):
            print(f"אזהרה: הקובץ {path} לא נמצא, מדלג עליו.")
            continue
        words = load_wordbank(path)
        print(f"{filename}: {len(words):,} ערכים.")
        merge_words(merged, words)

    write_wordbank(merged, OUTPUT_FILE)
    print(f"\nסך הכול {len(merged):,} ערכים ייחודיים במאגר הממוזג.")
    print(f"הקובץ {OUTPUT_FILE} מוכן לעבודה!")


if __name__ == "__main__":
    build_all_sources()
    print("\n=== ממזג את כל המקורות ===")
    merge_sources()