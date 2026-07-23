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
    load_resources_v3, resolve_fighter_name, compute_fighter_dynamic_states_v3,
    get_latest_fighter_profile_v3, STAT_COLS_V1, FEATURE_COLS_V3
)
from src.utils import fuzzy_match_fighter_name

model, raw_df, medians, all_fighters, model_path_used = load_resources_v3()
elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict = compute_fighter_dynamic_states_v3(raw_df)

print("=== INSPECTING JULY 18/19 2026 BASELINE EVENT IN DATASET ===")

# Search for fights on 2026-07-18 or 2026-07-19 in raw_df
july_df = raw_df[raw_df["event_date"].dt.strftime("%Y-%m-%d").str.startswith("2026-07-18") | 
                 raw_df["event_date"].dt.strftime("%Y-%m-%d").str.startswith("2026-07-19")].copy()

print(f"Found {len(july_df)} fights in raw_df for July 18/19 2026.")

processed_v3 = pd.read_csv("data/processed/ufc_features_delta_v3.csv")
processed_v3["event_date"] = pd.to_datetime(processed_v3["event_date"], errors="coerce")
july_v3 = processed_v3[processed_v3["event_date"].dt.strftime("%Y-%m-%d").str.startswith("2026-07-18") |
                       processed_v3["event_date"].dt.strftime("%Y-%m-%d").str.startswith("2026-07-19")].copy()
print(f"Found {len(july_v3)} fights in ufc_features_delta_v3.csv for July 18/19 2026.")

for idx, row in july_df.iterrows():
    f1 = row["f_1_name"]
    f2 = row["f_2_name"]
    winner = row["winner"]
    f1_odds = row.get("f_1_odds") or row.get("odds_f1")
    f2_odds = row.get("f_2_odds") or row.get("odds_f2")
    print(f"  Fight: {f1} vs {f2} | Winner: {winner} | Odds: {f1_odds} / {f2_odds}")
