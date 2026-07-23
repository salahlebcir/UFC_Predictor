import sys
import os
import unicodedata
import re
import difflib

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.utils import normalize_fighter_name, fuzzy_match_fighter_name

test_pairs = [
    ("Aleksandar Rakić", "Aleksandar Rakic"),
    ("Marcin Tybura", "Marcin Tybura"),
    ("Uroš Medić", "Uros Medic"),
    ("Vlasto Čepo", "Vlasto Cepo"),
    ("Mateusz Rębecki", "Mateusz Rebecki"),
    ("Édgar Cháirez", "Edgar Chairez"),
    ("Kauê Fernandes", "Kaue Fernandes"),
    ("Ian Machado Garry", "Ian Garry"),
    ("Edson Barboza Jr.", "Edson Barboza"),
    ("Steve Erceg", "Stephen Erceg")
]

print("=== VERIFYING UNICODE DIACRITICS AND GENERIC MATCHING ===")
for name1, name2 in test_pairs:
    norm1 = normalize_fighter_name(name1)
    norm2 = normalize_fighter_name(name2)
    matched = fuzzy_match_fighter_name(name1, [name2], threshold=0.75)
    print(f"[{name1:<20}] vs [{name2:<20}]")
    print(f"   Norm1: '{norm1}' | Norm2: '{norm2}' | Matched: {matched == name2}")
