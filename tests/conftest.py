import os
import sys

# src/ modules import each other with flat imports (e.g. `from grid import Grid`),
# so src/ must be on sys.path for the tests to import them the same way.
SRC_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
