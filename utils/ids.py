"""
utils/ids.py - Hex ID generation and tool-name normalisation.
"""

import re
import random


def generate_hex_id() -> str:
    """Generate a 6-digit uppercase hex ID."""
    return format(random.randint(0, 0xFFFFFF), '06X')

def ids_equal(id1: str, id2: str) -> bool:
    """IDs are equal regardless of case."""
    return id1.upper() == id2.upper()

def normalise(name: str) -> str:
    """
    Joins all words into a single lowercase string for comparison.
    'hello world' → 'helloworld'
    Also strips underscores and hyphens so 'g_it' == 'git'.
    """
    return re.sub(r'[\s_\-]', '', name).lower()

def fuzzy_name_match(query: str, candidate: str) -> bool:
    """
    Match tool names case-insensitively after stripping separators.
    'git' matches 'Git', 'G_it', 'g-it', 'GIT', etc.
    """
    return normalise(query) == normalise(candidate)
