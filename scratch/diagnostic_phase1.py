import os
import sys
import json
import pandas as pd
import numpy as np

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.predict import (
    load_resources_v3, compute_fighter_dynamic_states_v3,
    get_latest_fighter_profile_v3, resolve_fighter_name
)
from src.utils import normalize_fighter_name, fuzzy_match_fighter_name

model, raw_df, medians, all_fighters, model_path_used = load_resources_v3()
elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict = compute_fighter_dynamic_states_v3(raw_df)

cache_path = os.path.join(project_root, "data", "odds_cache.json")
with open(cache_path, "r", encoding="utf-8") as f:
    cache = json.load(f)

events = cache.get("events", [])

print(f"=== PHASE 1 DIAGNOSTIC: {len(events)} EVENTS IN CACHE ===")

card_fights = [ev for ev in events if "Ankalaev" in ev.get("event_title", "") or "2026-07-25" in ev.get("event_date", "")]

print(f"\n--- CARD 1: 2026-07-25 UFC Fight Night: Ankalaev vs. Guskov ({len(card_fights)} fights) ---")
for idx, ev in enumerate(card_fights, 1):
    f1 = ev.get("home_team")
    f2 = ev.get("away_team")
    bkms = ev.get("bookmakers", [])
    
    m1 = resolve_fighter_name(f1, all_fighters)
    m2 = resolve_fighter_name(f2, all_fighters)
    
    p1 = get_latest_fighter_profile_v3(m1, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if m1 else None
    p2 = get_latest_fighter_profile_v3(m2, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if m2 else None
    
    f1_exact_csv = f1 in all_fighters
    f2_exact_csv = f2 in all_fighters
    
    print(f"\n[{idx:02d}] {f1} vs {f2}")
    print(f"    F1 Exact in CSV: {f1_exact_csv:<5} | Resolved: '{m1}' | Profile: {p1 is not None}")
    print(f"    F2 Exact in CSV: {f2_exact_csv:<5} | Resolved: '{m2}' | Profile: {p2 is not None}")
    print(f"    Odds Count in Cache: {len(bkms)}")
