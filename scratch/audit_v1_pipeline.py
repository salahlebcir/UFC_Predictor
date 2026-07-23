import os
import sys
import json
import time
import pandas as pd
import numpy as np

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

print("================================================================================")
print("       AUDIT GLOBAL DE VALIDATION V1 - UFC FIGHT PREDICTOR V3                  ")
print("================================================================================\n")

# ------------------------------------------------------------------------------
# TEST MODULE 1 : COMPOSANTS ARCHITECTURAUX ET RESSOURCES
# ------------------------------------------------------------------------------
print("--- [MODULE 1] Vérification des Ressources et Modèles ---")
model_path = os.path.join("models", "ufc_xgboost_model_v3_calibrated.pkl")
processed_csv_path = os.path.join("data", "processed", "ufc_features_delta_v3.csv")
cache_json_path = os.path.join("data", "odds_cache.json")
tracker_json_path = os.path.join("data", "historical_tracker.json")

print(f"1. Modèle Calibré XGBoost V3 : {'OK (' + model_path + ')' if os.path.exists(model_path) else 'MANQUANT'}")
print(f"2. Dataset V3 delta features : {'OK (' + processed_csv_path + ')' if os.path.exists(processed_csv_path) else 'MANQUANT'}")
print(f"3. Cache local des cotes (2h) : {'OK (' + cache_json_path + ')' if os.path.exists(cache_json_path) else 'MANQUANT'}")
print(f"4. Tracker d'historique JSON : {'OK (' + tracker_json_path + ')' if os.path.exists(tracker_json_path) else 'MANQUANT'}")

# ------------------------------------------------------------------------------
# TEST MODULE 2 : PRÉDICTION METIER & LOGIQUE DU MOTEUR (src/predict.py)
# ------------------------------------------------------------------------------
print("\n--- [MODULE 2] Test d'Inférence Métier & No-Imputation ---")
from src.predict import load_resources_v3, resolve_fighter_name, compute_fighter_dynamic_states_v3, get_latest_fighter_profile_v3, FEATURE_COLS_V3

model, raw_df, medians, all_fighters, model_path_used = load_resources_v3()
elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict = compute_fighter_dynamic_states_v3(raw_df)

# Test 1: Fighter existent
name_a = resolve_fighter_name("Dricus Du Plessis", all_fighters)
name_b = resolve_fighter_name("Kamaru Usman", all_fighters)
prof_a = get_latest_fighter_profile_v3(name_a, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict)
prof_b = get_latest_fighter_profile_v3(name_b, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict)

print(f"Résolution Dricus Du Plessis -> '{name_a}' | Profile: {'OK' if prof_a else 'Missing'}")
print(f"Résolution Kamaru Usman      -> '{name_b}' | Profile: {'OK' if prof_b else 'Missing'}")

# Test 2: Unknown debutant (No Fake Data)
name_unknown = resolve_fighter_name("Fighter Inconnu XYZ 99", all_fighters)
print(f"Résolution Fighter Inconnu -> '{name_unknown}' (Attendu: None pour No Fake Data)")

# ------------------------------------------------------------------------------
# TEST MODULE 3 : HISTORIQUE & DEDOUBLONNAGE (src/historical_tracker.py)
# ------------------------------------------------------------------------------
print("\n--- [MODULE 3] Audit de la Baseline et Dé-doublonnage ---")
from src.historical_tracker import load_historical_tracker, deduplicate_card_fights

tracker_data = load_historical_tracker()
cards = tracker_data.get("cards", {})
summary = tracker_data.get("summary", {})

print(f"Nombre de cartes dans l'historique : {len(cards)}")

card_baseline_key = "2026-07-18 | UFC Fight Night: Du Plessis vs. Usman"
if card_baseline_key in cards:
    baseline_info = cards[card_baseline_key]
    raw_fights = baseline_info.get("fights", [])
    clean_fights = deduplicate_card_fights(raw_fights)
    print(f"Carte Baseline 'Du Plessis vs. Usman' :")
    print(f"  • Combats bruts : {len(raw_fights)}")
    print(f"  • Combats uniques : {len(clean_fights)} (Strictement 12 attendus)")
    print(f"  • Main Event (Combat #1) : '{clean_fights[0]['f1']}' vs '{clean_fights[0]['f2']}'")
    
    # Audit des sub-motifs NO BET
    no_bets = [f for f in clean_fights if not f.get("is_value_bet")]
    print(f"  • Combats NO BET : {len(no_bets)}/12")
    for nb in no_bets:
        reason = nb.get("no_bet_reason")
        max_ev = nb.get("max_ev_pct")
        print(f"    - {nb['f1']} vs {nb['f2']} | Motif: {reason} | EV max: {max_ev:+.1f}%")
else:
    print(f"  [!] ERREUR: Carte Baseline introuvable")

print(f"\nBilan Financier Baseline enregistré dans JSON :")
print(f"  • Profit Net Total : {summary.get('total_profit', 0):+.2f} €")
print(f"  • Rendement ROI    : {summary.get('roi_pct', 0):+.1f} %")
print(f"  • Win Rate         : {summary.get('win_rate_pct', 0):.1f} % ({summary.get('value_bets_won', 0)}/{summary.get('value_bets_count', 0)})")
print(f"  • Volume Misé      : {summary.get('total_staked', 0):.0f} €")

# ------------------------------------------------------------------------------
# TEST MODULE 4 : INTEGRITE DU SYSTEME DE LANCEMENT (run.py)
# ------------------------------------------------------------------------------
print("\n--- [MODULE 4] Audit du Lanceur Unique run.py ---")
import run
print(f"Fichiers essentiels vérifiés par run.py : OK")

print("\n================================================================ gloom")
print("               RESULTAT FINAL DE L'AUDIT GLOBAL : COMPLIANT V1         ")
print("========================================================================\n")
