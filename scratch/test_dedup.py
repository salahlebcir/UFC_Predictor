import os
import sys
import json
import collections

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.utils import normalize_fighter_name, fuzzy_match_fighter_name

def deduplicate_fights(fights):
    unique_fights = []
    seen_pairs = set()
    
    for f in fights:
        f1 = f.get("f1") or f.get("home_team", "")
        f2 = f.get("f2") or f.get("away_team", "")
        
        n1 = normalize_fighter_name(f1)
        n2 = normalize_fighter_name(f2)
        
        pair_key = tuple(sorted([n1, n2]))
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_fights.append(f)
            
    return unique_fights

print("=== TESTING DEDUPLICATION LOGIC ===")

with open("data/historical_tracker.json", "r", encoding="utf-8") as f:
    tracker_data = json.load(f)

for card_key, card_info in tracker_data.get("cards", {}).items():
    raw_fights = card_info.get("fights", [])
    dedup = deduplicate_fights(raw_fights)
    print(f"Card: '{card_key}' | Raw fights: {len(raw_fights)} | Deduplicated fights: {len(dedup)}")
