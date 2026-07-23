import os
import sys
import json
import pandas as pd
import numpy as np

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Reconfigure encoding
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.predict import (
    load_resources_v3, compute_fighter_dynamic_states_v3,
    get_latest_fighter_profile_v3, resolve_fighter_name
)
from src.utils import normalize_fighter_name, fuzzy_match_fighter_name, is_token_set_match

model, raw_df, medians, all_fighters, model_path_used = load_resources_v3()
elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict = compute_fighter_dynamic_states_v3(raw_df)

cache_path = os.path.join(project_root, "data", "odds_cache.json")
with open(cache_path, "r", encoding="utf-8") as f:
    cache = json.load(f)

events = cache.get("events", [])
print(f"Total events in cache: {len(events)}")

from collections import defaultdict
grouped = defaultdict(list)
for ev in events:
    date_str = ev.get("event_date", ev.get("commence_time", "")[:10])
    title = ev.get("event_title", "UFC Event")
    grouped[f"{date_str} | {title}"].append(ev)

total_fights = 0
ok_fights = 0
none_fights = 0

for card_key, fights in grouped.items():
    print("=" * 80)
    print(f"CARD: {card_key} ({len(fights)} fights)")
    print("=" * 80)
    for idx, ev in enumerate(fights, 1):
        total_fights += 1
        f1_raw = ev.get("home_team", "")
        f2_raw = ev.get("away_team", "")
        
        name_a = resolve_fighter_name(f1_raw, all_fighters)
        name_b = resolve_fighter_name(f2_raw, all_fighters)
        
        p1 = get_latest_fighter_profile_v3(name_a, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if name_a else None
        p2 = get_latest_fighter_profile_v3(name_b, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if name_b else None
        
        # Check odds extraction logic in app.py
        bookmakers = ev.get("bookmakers", [])
        best_o_a, best_o_b = None, None
        targets = [t for t in [name_a, name_b, f1_raw, f2_raw] if t]
        
        for bkm in bookmakers:
            for mkt in bkm.get("markets", []):
                if mkt.get("key") == "h2h":
                    outcomes = mkt.get("outcomes", [])
                    omap = {}
                    for o in outcomes:
                        oname = o.get("name", "")
                        oprice = float(o.get("price", 0.0))
                        if oname and oprice > 1.0:
                            matched = fuzzy_match_fighter_name(oname, targets, threshold=0.70)
                            if matched:
                                omap[matched] = oprice
                    o_a = omap.get(name_a) or omap.get(f1_raw)
                    o_b = omap.get(name_b) or omap.get(f2_raw)
                    if o_a and o_b:
                        if best_o_a is None or (o_a + o_b > best_o_a + best_o_b):
                            best_o_a = o_a
                            best_o_b = o_b

        reasons = []
        if not name_a:
            reasons.append(f"Fighter A name resolution failed for '{f1_raw}'")
        elif p1 is None:
            reasons.append(f"Fighter A profile missing in CSV for '{f1_raw}' (resolved as '{name_a}')")
            
        if not name_b:
            reasons.append(f"Fighter B name resolution failed for '{f2_raw}'")
        elif p2 is None:
            reasons.append(f"Fighter B profile missing in CSV for '{f2_raw}' (resolved as '{name_b}')")
            
        if not best_o_a or not best_o_b or best_o_a <= 1.0 or best_o_b <= 1.0:
            reasons.append(f"Odds extraction failed for '{f1_raw}' vs '{f2_raw}' (odds_a={best_o_a}, odds_b={best_o_b})")
            
        if reasons:
            none_fights += 1
            print(f"[{idx:02d}] {f1_raw} vs {f2_raw} ==> STATUS: NONE | Reasons: {reasons}")
        else:
            ok_fights += 1
            print(f"[{idx:02d}] {f1_raw} vs {f2_raw} ==> STATUS: OK | Odds: {best_o_a:.2f} / {best_o_b:.2f}")

print("\n" + "="*80)
print(f"SUMMARY: Total Fights = {total_fights} | OK = {ok_fights} | NONE = {none_fights}")
print("="*80)
