import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from hebrew_utils import fetch_titles_from_dump, write_wordbank

DUMPS_URL = "https://dumps.wikimedia.org/hewiki/latest/hewiki-latest-all-titles-in-ns0.gz"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sources", "wikipedia_he.txt")


def build_crossword_bank():
    words = fetch_titles_from_dump(DUMPS_URL, "ויקיפדיה העברית")
    write_wordbank(words, OUTPUT_FILE)
    print(f"הקובץ {OUTPUT_FILE} מוכן לעבודה!")


if __name__ == "__main__":
    build_crossword_bank()