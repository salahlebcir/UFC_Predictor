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
from src.utils import normalize_fighter_name, fuzzy_match_fighter_name
from src.historical_tracker import save_historical_tracker, deduplicate_card_fights

print("=== RE-EVALUATING EXACT METHODOLOGY & PURGING ALL DUPLICATES ===")

model, raw_df, medians, all_fighters, model_path_used = load_resources_v3()
elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict = compute_fighter_dynamic_states_v3(raw_df)

# Exact official UFC.com fights & exact decimal converted odds
official_baseline_fights = [
    # 1. Main Event
    {"f1": "Dricus Du Plessis", "f2": "Kamaru Usman", "odds_a": 1.43, "odds_b": 2.80, "winner": "Dricus Du Plessis", "bkm": "UFC.com / Market Odds"},
    # 2. Co-Main Event
    {"f1": "Christian Leroy Duncan", "f2": "Jared Cannonier", "odds_a": 1.29, "odds_b": 3.70, "winner": "Christian Leroy Duncan", "bkm": "UFC.com / Market Odds"},
    # 3. Prelims
    {"f1": "Chase Hooper", "f2": "Mitch Ramirez", "odds_a": 1.26, "odds_b": 3.80, "winner": "Chase Hooper", "bkm": "UFC.com / Market Odds"},
    {"f1": "Fatima Kline", "f2": "Tabatha Ricci", "odds_a": 1.20, "odds_b": 4.50, "winner": "Fatima Kline", "bkm": "UFC.com / Market Odds"},
    {"f1": "Tommy McMillen", "f2": "Alberto Montes", "odds_a": 1.50, "odds_b": 2.55, "winner": "Tommy McMillen", "bkm": "UFC.com / Market Odds"},
    {"f1": "Jose Delgado", "f2": "Austin Bashi", "odds_a": 2.15, "odds_b": 1.69, "winner": "Jose Delgado", "bkm": "UFC.com / Market Odds"},
    {"f1": "Jean-Paul Lebosnoyani", "f2": "Seokhyeon Ko", "odds_a": 2.50, "odds_b": 1.53, "winner": "Jean-Paul Lebosnoyani", "bkm": "UFC.com / Market Odds"},
    {"f1": "Felipe Franco", "f2": "Levi Rodrigues Jr.", "odds_a": 2.25, "odds_b": 1.63, "winner": "Felipe Franco", "bkm": "UFC.com / Market Odds"},
    {"f1": "Ezra Elliott", "f2": "Damien Anderson", "odds_a": 2.05, "odds_b": 1.74, "winner": "Ezra Elliott", "bkm": "UFC.com / Market Odds"},
    {"f1": "Alden Coria", "f2": "Stewart Nicoll", "odds_a": 1.08, "odds_b": 7.75, "winner": "Alden Coria", "bkm": "UFC.com / Market Odds"},
    {"f1": "RJ Harris", "f2": "Alvin Hines", "odds_a": 2.00, "odds_b": 1.80, "winner": "RJ Harris", "bkm": "UFC.com / Market Odds"},
    {"f1": "Dione Barbosa", "f2": "Anna Melisano", "odds_a": 1.15, "odds_b": 5.25, "winner": "Dione Barbosa", "bkm": "UFC.com / Market Odds"}
]

fights_list = []

for idx, item in enumerate(official_baseline_fights):
    f1_raw = item["f1"]
    f2_raw = item["f2"]
    odds_a = item["odds_a"]
    odds_b = item["odds_b"]
    winner_official = item["winner"]
    bkm_name = item["bkm"]
    label = "MAIN EVENT" if idx == 0 else ("CO-MAIN EVENT" if idx == 1 else f"Combat #{idx + 1}")

    name_a = resolve_fighter_name(f1_raw, all_fighters)
    name_b = resolve_fighter_name(f2_raw, all_fighters)

    profile_a = get_latest_fighter_profile_v3(name_a, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if name_a else None
    profile_b = get_latest_fighter_profile_v3(name_b, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if name_b else None

    has_full_data = bool(name_a and name_b and profile_a is not None and profile_b is not None)
    has_valid_odds = bool(odds_a and odds_b and odds_a > 1.0 and odds_b > 1.0)

    pct_a, pct_b = None, None
    ev_a, ev_b = None, None
    is_value_bet = False
    bet_fighter = None
    bet_odds = None
    bet_prob = None

    if has_full_data:
        delta_dict = {}
        for stat in STAT_COLS_V1:
            delta_key = f"delta_{stat}"
            val_a, val_b = profile_a[stat], profile_b[stat]
            delta_dict[delta_key] = (val_a - val_b) if (pd.notna(val_a) and pd.notna(val_b)) else medians.get(delta_key, 0.0)

        delta_dict["delta_elo"] = profile_a["elo"] - profile_b["elo"]
        delta_dict["delta_win_streak"] = profile_a["win_streak"] - profile_b["win_streak"]
        delta_dict["delta_loss_streak"] = profile_a["loss_streak"] - profile_b["loss_streak"]
        delta_dict["delta_win_rate_last_5"] = profile_a["win_rate_5"] - profile_b["win_rate_5"]
        delta_dict["delta_ufc_win_rate"] = profile_a["ufc_win_rate"] - profile_b["ufc_win_rate"]
        delta_dict["delta_ufc_fights"] = profile_a["ufc_fights"] - profile_b["ufc_fights"]
        delta_dict["delta_rank"] = profile_b["rank"] - profile_a["rank"]
        delta_dict["is_ranked_f1"] = profile_a["is_ranked"]
        delta_dict["is_ranked_f2"] = profile_b["is_ranked"]
        delta_dict["delta_win_rate_3y"] = profile_a["wr_3y"] - profile_b["wr_3y"]
        delta_dict["delta_SlpM_3y"] = (profile_a["slpm_3y"] - profile_b["slpm_3y"]) if (pd.notna(profile_a["slpm_3y"]) and pd.notna(profile_b["slpm_3y"])) else medians.get("delta_SlpM_3y", 0.0)
        delta_dict["delta_SApM_3y"] = (profile_a["sapm_3y"] - profile_b["sapm_3y"]) if (pd.notna(profile_a["sapm_3y"]) and pd.notna(profile_b["sapm_3y"])) else medians.get("delta_SApM_3y", 0.0)
        delta_dict["delta_TD_Def_3y"] = (profile_a["td_def_3y"] - profile_b["td_def_3y"]) if (pd.notna(profile_a["td_def_3y"]) and pd.notna(profile_b["td_def_3y"])) else medians.get("delta_TD_Def_3y", 0.0)

        # REALS PREDICTIONS FROM XGBOOST V3 CALIBRATED MODEL
        X_input = pd.DataFrame([delta_dict])[FEATURE_COLS_V3]
        probs = model.predict_proba(X_input)[0]
        prob_b_loss, prob_a_win = probs[0], probs[1]
        pct_a = float(prob_a_win * 100.0)
        pct_b = float(prob_b_loss * 100.0)

        if has_valid_odds:
            # EV ALGORITHM ON BOTH FIGHTERS
            ev_a = float((prob_a_win * odds_a) - 1.0)
            ev_b = float((prob_b_loss * odds_b) - 1.0)
            best_ev = max(ev_a, ev_b)
            if best_ev > 0.20:
                is_value_bet = True
                bet_fighter = f1_raw if ev_a >= ev_b else f2_raw
                bet_odds = odds_a if ev_a >= ev_b else odds_b
                bet_prob = float(prob_a_win if ev_a >= ev_b else prob_b_loss)

    res_status = None
    net_gain = 0.0
    if is_value_bet and winner_official:
        is_win = (fuzzy_match_fighter_name(winner_official, [bet_fighter], threshold=0.75) is not None)
        if is_win:
            res_status = "WIN"
            net_gain = float(10.0 * (bet_odds - 1.0))
        else:
            res_status = "LOSS"
            net_gain = -10.0

    fight_obj = {
        "fight_index": idx,
        "fight_label": label,
        "f1": f1_raw,
        "f2": f2_raw,
        "has_full_data": has_full_data,
        "has_valid_odds": has_valid_odds,
        "pct_a": pct_a,
        "pct_b": pct_b,
        "odds_a": odds_a,
        "odds_b": odds_b,
        "bkm_name": bkm_name,
        "ev_a": ev_a,
        "ev_b": ev_b,
        "is_value_bet": is_value_bet,
        "bet_fighter": bet_fighter,
        "bet_odds": bet_odds,
        "bet_prob": bet_prob,
        "winner": winner_official,
        "result_status": res_status,
        "net_gain": net_gain
    }
    fights_list.append(fight_obj)

# Ensure strict deduplication of fights_list
fights_list = deduplicate_card_fights(fights_list)

card_key = "2026-07-18 | UFC Fight Night: Du Plessis vs. Usman"

cards_map = {
    card_key: {
        "event_title": "UFC Fight Night: Du Plessis vs. Usman",
        "event_date": "2026-07-18",
        "is_completed": True,
        "fights": fights_list
    }
}

total_staked = 0.0
total_profit = 0.0
value_bets_count = 0
value_bets_won = 0

for f in fights_list:
    if f.get("is_value_bet") and f.get("winner"):
        total_staked += 10.0
        value_bets_count += 1
        if f.get("result_status") == "WIN":
            value_bets_won += 1
            total_profit += f.get("net_gain", 0.0)
        elif f.get("result_status") == "LOSS":
            total_profit += f.get("net_gain", -10.0)

roi_pct = (total_profit / total_staked * 100.0) if total_staked > 0 else 0.0
win_rate_pct = (value_bets_won / value_bets_count * 100.0) if value_bets_count > 0 else 0.0

summary = {
    "total_profit": total_profit,
    "total_staked": total_staked,
    "roi_pct": roi_pct,
    "win_rate_pct": win_rate_pct,
    "value_bets_count": value_bets_count,
    "value_bets_won": value_bets_won
}

tracker_data = {
    "cards": cards_map,
    "summary": summary
}

save_historical_tracker(tracker_data)

print(f"Pushed clean data to {os.path.abspath('data/historical_tracker.json')}")
print(f"Unique fights count: {len(fights_list)}")
print(f"Summary: Profit={total_profit:+.2f}€ | ROI={roi_pct:+.1f}% | WinRate={win_rate_pct:.1f}% ({value_bets_won}/{value_bets_count})")
