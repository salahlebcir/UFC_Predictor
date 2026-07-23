import os
import sys
import json
import pandas as pd

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.predict import load_resources_v3, resolve_fighter_name
from src.odds_api import get_cached_or_fresh_odds
from src.historical_tracker import sync_historical_tracker
from app import extract_fight_odds

print("=== DIAGNOSING ODDS DATA FLOW ===")

events, from_cache, age_hours = get_cached_or_fresh_odds()
print(f"Loaded {len(events)} raw events from cache (age: {age_hours:.2f}h).")

# Inspect raw event for Ankalaev
for ev in events:
    h = ev.get("home_team", "")
    a = ev.get("away_team", "")
    if "Ankalaev" in h or "Ankalaev" in a:
        bkms = ev.get("bookmakers", [])
        print(f"\n[RAW CACHE EVENT]: {h} vs {a} | Bookmakers: {len(bkms)}")
        o_a, o_b, bkm = extract_fight_odds(ev, h, a)
        print(f"   extract_fight_odds result on raw event: odds_a={o_a}, odds_b={o_b}, bkm={bkm}")

model, raw_df, medians, all_fighters, model_path_used = load_resources_v3()
upcoming_cards, past_cards, summary = sync_historical_tracker(events, raw_df, model, medians, all_fighters)

print(f"\n[TRACKER PROCESSED UPCOMING CARDS]: {len(upcoming_cards)}")

for card_key, card_info in upcoming_cards.items():
    if "Ankalaev" in card_key:
        print(f"\nCARD: {card_key}")
        for fight in card_info.get("fights", []):
            f1 = fight.get("f1") or fight.get("home_team", "")
            f2 = fight.get("f2") or fight.get("away_team", "")
            has_valid = fight.get("has_valid_odds")
            oa = fight.get("odds_a")
            ob = fight.get("odds_b")
            bkm = fight.get("bkm_name")
            print(f"  Fight: {f1} vs {f2}")
            print(f"     in tracker dict: has_valid={has_valid}, odds_a={oa}, odds_b={ob}, bkm={bkm}")
            # Try running extract_fight_odds on tracker dict
            res_a, res_b, res_bkm = extract_fight_odds(fight, f1, f2)
            print(f"     extract_fight_odds(fight_dict): odds_a={res_a}, odds_b={res_b}, bkm={res_bkm}")
