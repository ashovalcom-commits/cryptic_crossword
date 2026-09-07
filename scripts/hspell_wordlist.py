import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from hebrew_utils import fetch_hspell_base_words, write_wordbank

# מילון היסוד של Hspell (ללא צירופי תחיליות דקדוקיות כמו "ו", "כש", "וב"),
# בפורמט Hunspell, כפי שמתוחזק בפרויקט המילונים של LibreOffice.
DIC_URL = "https://raw.githubusercontent.com/LibreOffice/dictionaries/master/he_IL/he_IL.dic"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "sources", "hspell_he.txt")


def build_crossword_bank():
    words = fetch_hspell_base_words(DIC_URL, "מילון Hspell (he_IL)")
    write_wordbank(words, OUTPUT_FILE)
    print(f"הקובץ {OUTPUT_FILE} מוכן לעבודה!")


if __name__ == "__main__":
    build_crossword_bank()
