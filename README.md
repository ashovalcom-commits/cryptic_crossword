# Cryptic Crossword

A small project for working with a Hebrew cryptic crossword wordbank and related puzzle-generation tooling.

## Project structure

- `data/` – word bank and supporting data files
- `scripts/` – utility scripts
- `src/` – source code

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run scripts from the project root as needed, for example:

```bash
python scripts/wikipedia_title.py
```

### Building the word bank

The crossword word bank (`data/crossword_wordbank_he.txt`) is built from several
sources, each fetched by its own script and saved separately under
`data/sources/`:

- `scripts/wikipedia_title.py` – Hebrew Wikipedia article titles (includes redirects).
- `scripts/wiktionary_title.py` – Hebrew Wiktionary entry titles.
- `scripts/hspell_wordlist.py` – Hspell's base word dictionary (via the
  LibreOffice-maintained `he_IL` Hunspell dictionary), covering standard
  Hebrew vocabulary beyond proper nouns/titles.

To fetch all sources and rebuild the merged word bank in one step:

```bash
python scripts/build_wordbank.py
```

## Notes

This repository is a starting point for crossword-related tooling and data experiments. Expand the README as the project grows.
