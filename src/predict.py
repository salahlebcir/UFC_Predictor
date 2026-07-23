"""
Script CLI interactif et de prédiction pour les combats UFC - MODULE V3 CALIBRÉ & FINANCIER.
Charge le modèle XGBoost V3 Calibré (Sigmoïde / Platt Scaling),
reconstruit dynamiquement l'état des combattants (Elo, Forme, Palmarès, Rang [0.0 = Champion], Fenêtres 36 mois),
récupère automatiquement les cotes via The Odds API avec cache local (12h),
et calcule l'EV (Expected Value) et la détection de Value Bets (Seuil optimal +20.0%).
Règle stricte d'absence d'imputation (No Fake Data) : Bascule en STATUT NONE si données incomplètes.
"""

import os
import sys
import json
import argparse
import difflib
import collections
import re
import joblib
import pandas as pd
import numpy as np

# Module de gestion des utilitaires et des cotes
try:
    from src.odds_api import get_odds_for_match
    from src.utils import normalize_fighter_name, fuzzy_match_fighter_name, is_token_set_match
except ImportError:
    from odds_api import get_odds_for_match
    from utils import normalize_fighter_name, fuzzy_match_fighter_name, is_token_set_match

# System stdout encoding fallback for Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Paths
RAW_DATA_PATH = os.path.join("data", "raw", "UFC_full_data_silver_v2.csv")
MODEL_CALIBRATED_PATH = os.path.join("models", "ufc_xgboost_model_v3_calibrated.pkl")
MODEL_V3_PATH = os.path.join("models", "ufc_xgboost_model_v3.pkl")
MEDIANS_V3_PATH = os.path.join("data", "processed", "feature_medians_v3.json")

# Stat names and labels map
STAT_COLS_V1 = [
    "reach_cm", "height_cm", "age",
    "SlpM", "Str_Acc", "SApM", "Str_Def",
    "TD_Avg", "TD_Acc", "TD_Def", "Sub_Avg"
]

FEATURE_COLS_V3 = [
    "delta_reach_cm", "delta_height_cm", "delta_age",
    "delta_SlpM", "delta_Str_Acc", "delta_SApM", "delta_Str_Def",
    "delta_TD_Avg", "delta_TD_Acc", "delta_TD_Def", "delta_Sub_Avg",
    "delta_elo", "delta_win_streak", "delta_loss_streak", "delta_win_rate_last_5",
    "delta_ufc_win_rate", "delta_ufc_fights", "delta_rank", "is_ranked_f1", "is_ranked_f2",
    "delta_win_rate_3y", "delta_SlpM_3y", "delta_SApM_3y", "delta_TD_Def_3y"
]

DELTA_LABELS_MAP = {
    "delta_reach_cm": "Allonge (Reach cm)",
    "delta_height_cm": "Taille (Height cm)",
    "delta_age": "Age (Annees)",
    "delta_SlpM": "Coups connectes / min (SlpM)",
    "delta_Str_Acc": "Precision de frappe (Str. Acc.)",
    "delta_SApM": "Coups encaisses / min (SApM - Vulnerabilite)",
    "delta_Str_Def": "Defense contre les coups (Str. Def.)",
    "delta_TD_Avg": "Moyenne d'amenees au sol / 15 min (TD Avg)",
    "delta_TD_Acc": "Precision des takedowns (TD Acc.)",
    "delta_TD_Def": "Defense de takedown (TD Def.)",
    "delta_Sub_Avg": "Tentatives de soumission / 15 min (Sub Avg)",
    "delta_elo": "Score Elo Historique UFC",
    "delta_win_streak": "Serie de victoires consecutives",
    "delta_loss_streak": "Serie de defaites consecutives",
    "delta_win_rate_last_5": "Taux de victoire sur les 5 derniers combats",
    "delta_ufc_win_rate": "Taux de victoire global en carriere UFC",
    "delta_ufc_fights": "Nombre total de combats disputés a l'UFC",
    "delta_rank": "Classement Officiel UFC (Difference de Rang)",
    "is_ranked_f1": "Combattant A fait partie du Top 15 UFC",
    "is_ranked_f2": "Combattant B fait partie du Top 15 UFC",
    "delta_win_rate_3y": "Taux de victoire sur les 3 dernieres annees",
    "delta_SlpM_3y": "Coups connectes/min sur les 3 dernieres annees",
    "delta_SApM_3y": "Coups encaisses/min sur les 3 dernieres annees",
    "delta_TD_Def_3y": "Defense de takedown sur les 3 dernieres annees"
}


def load_resources_v3():
    """Charge le modèle V3 (calibré si disponible), les données brutes et les médianes V3."""
    target_model_path = MODEL_CALIBRATED_PATH if os.path.exists(MODEL_CALIBRATED_PATH) else MODEL_V3_PATH
    if not os.path.exists(target_model_path):
        raise FileNotFoundError(f"Aucun modèle trouvé dans {target_model_path}. Entraînez-le via src/train.py ou src/calibrate_model.py.")
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Les données brutes {RAW_DATA_PATH} sont introuvables.")

    model = joblib.load(target_model_path)
    raw_df = pd.read_csv(RAW_DATA_PATH, low_memory=False)
    raw_df["event_date"] = pd.to_datetime(raw_df["event_date"], errors="coerce")
    raw_df = raw_df.sort_values(by="event_date", ascending=True).reset_index(drop=True)

    medians = {}
    if os.path.exists(MEDIANS_V3_PATH):
        with open(MEDIANS_V3_PATH, "r", encoding="utf-8") as f:
            medians = json.load(f)

    f1_names = raw_df["f_1_name"].dropna().unique()
    f2_names = raw_df["f_2_name"].dropna().unique()
    all_fighters = sorted(list(set(f1_names).union(set(f2_names))))

    return model, raw_df, medians, all_fighters, target_model_path


def resolve_fighter_name(user_input, all_fighters):
    """Recherche tolérante et générique via fuzzy_match_fighter_name."""
    return fuzzy_match_fighter_name(user_input, all_fighters, threshold=0.75)


def compute_fighter_dynamic_states_v3(raw_df):
    """Reconstruit l'état dynamique V3 (Elo, Forme, Palmarès, Rang [0.0 = Champion], Fenêtres 3 ans)."""
    elo_dict = collections.defaultdict(lambda: 1500.0)
    history_dict = collections.defaultdict(list)
    win_streak_dict = collections.defaultdict(int)
    loss_streak_dict = collections.defaultdict(int)
    latest_rank_dict = {}

    df_valid = raw_df.dropna(subset=["winner"]).copy()

    for idx, row in df_valid.iterrows():
        f1 = row["f_1_name"]
        f2 = row["f_2_name"]
        winner = row["winner"]
        event_dt = row["event_date"]

        raw_r1 = pd.to_numeric(row.get("f_1_ranking"), errors="coerce")
        raw_r2 = pd.to_numeric(row.get("f_2_ranking"), errors="coerce")

        # 0.0 correspond au rang de Champion dans les données UFC
        if pd.notna(raw_r1) and 0.0 <= raw_r1 <= 15.0:
            latest_rank_dict[f1] = raw_r1
        if pd.notna(raw_r2) and 0.0 <= raw_r2 <= 15.0:
            latest_rank_dict[f2] = raw_r2

        f1_won = (winner == f1)

        elo_f1 = elo_dict[f1]
        elo_f2 = elo_dict[f2]

        S1 = 1.0 if f1_won else 0.0
        S2 = 0.0 if f1_won else 1.0

        E1 = 1.0 / (1.0 + 10.0 ** ((elo_f2 - elo_f1) / 400.0))
        E2 = 1.0 - E1

        elo_dict[f1] += 32.0 * (S1 - E1)
        elo_dict[f2] += 32.0 * (S2 - E2)

        slpm_f1 = pd.to_numeric(row.get("f_1_fighter_SlpM"), errors="coerce")
        sapm_f1 = pd.to_numeric(row.get("f_1_fighter_SApM"), errors="coerce")
        td_def_f1 = pd.to_numeric(row.get("f_1_fighter_TD_Def"), errors="coerce")

        slpm_f2 = pd.to_numeric(row.get("f_2_fighter_SlpM"), errors="coerce")
        sapm_f2 = pd.to_numeric(row.get("f_2_fighter_SApM"), errors="coerce")
        td_def_f2 = pd.to_numeric(row.get("f_2_fighter_TD_Def"), errors="coerce")

        history_dict[f1].append({
            "date": event_dt, "outcome": "W" if f1_won else "L",
            "SlpM": slpm_f1, "SApM": sapm_f1, "TD_Def": td_def_f1
        })
        history_dict[f2].append({
            "date": event_dt, "outcome": "L" if f1_won else "W",
            "SlpM": slpm_f2, "SApM": sapm_f2, "TD_Def": td_def_f2
        })

        if f1_won:
            win_streak_dict[f1] += 1
            loss_streak_dict[f1] = 0
            loss_streak_dict[f2] += 1
            win_streak_dict[f2] = 0
        else:
            loss_streak_dict[f1] += 1
            win_streak_dict[f1] = 0
            win_streak_dict[f2] += 1
            loss_streak_dict[f2] = 0

    return elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict


def get_latest_fighter_profile_v3(fighter_name, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict):
    """Extrait le profil V1 + V2 + V3 le plus récent d'un combattant."""
    sub_df1 = raw_df[raw_df["f_1_name"] == fighter_name].copy()
    sub_df2 = raw_df[raw_df["f_2_name"] == fighter_name].copy()

    recent_f1 = sub_df1.sort_values(by="event_date", ascending=False).iloc[0] if len(sub_df1) > 0 else None
    recent_f2 = sub_df2.sort_values(by="event_date", ascending=False).iloc[0] if len(sub_df2) > 0 else None

    if recent_f1 is None and recent_f2 is None:
        return None

    if recent_f1 is not None and recent_f2 is not None:
        date1 = recent_f1["event_date"]
        date2 = recent_f2["event_date"]
        chosen = recent_f1 if (pd.notna(date1) and date1 >= date2) else recent_f2
        is_f1 = (chosen is recent_f1)
    elif recent_f1 is not None:
        chosen = recent_f1
        is_f1 = True
    else:
        chosen = recent_f2
        is_f1 = False

    prefix = "f_1_fighter_" if is_f1 else "f_2_fighter_"

    # V1
    reach = pd.to_numeric(chosen[f"{prefix}reach_cm"], errors="coerce")
    height = pd.to_numeric(chosen[f"{prefix}height_cm"], errors="coerce")
    dob_val = pd.to_datetime(chosen[f"{prefix}dob"], errors="coerce")
    current_date = pd.Timestamp.now()
    age = (current_date - dob_val).days / 365.25 if pd.notna(dob_val) else np.nan

    slpm = pd.to_numeric(chosen[f"{prefix}SlpM"], errors="coerce")
    str_acc = pd.to_numeric(chosen[f"{prefix}Str_Acc"], errors="coerce")
    sapm = pd.to_numeric(chosen[f"{prefix}SApM"], errors="coerce")
    str_def = pd.to_numeric(chosen[f"{prefix}Str_Def"], errors="coerce")
    td_avg = pd.to_numeric(chosen[f"{prefix}TD_Avg"], errors="coerce")
    td_acc = pd.to_numeric(chosen[f"{prefix}TD_Acc"], errors="coerce")
    td_def = pd.to_numeric(chosen[f"{prefix}TD_Def"], errors="coerce")
    sub_avg = pd.to_numeric(chosen[f"{prefix}Sub_Avg"], errors="coerce")

    # V2
    elo = elo_dict[fighter_name]
    hist = history_dict[fighter_name]
    win_streak = win_streak_dict[fighter_name]
    loss_streak = loss_streak_dict[fighter_name]

    if len(hist) == 0:
        return None

    last5 = [h["outcome"] for h in hist[-5:]] if len(hist) > 0 else []
    win_rate_5 = last5.count("W") / len(last5) if len(last5) > 0 else 0.5

    ufc_fights = len(hist)
    all_outcomes = [h["outcome"] for h in hist]
    ufc_win_rate = all_outcomes.count("W") / ufc_fights if ufc_fights > 0 else 0.5

    raw_rank = latest_rank_dict.get(fighter_name, np.nan)
    rank = raw_rank if (pd.notna(raw_rank) and 0.0 <= raw_rank <= 15.0) else 20.0
    is_ranked = 1.0 if rank <= 15.0 else 0.0

    # V3 (3-year rolling stats)
    three_years_ago = current_date - pd.DateOffset(years=3)
    hist_3y = [h for h in hist if h["date"] >= three_years_ago]

    if len(hist_3y) > 0:
        outcomes_3y = [h["outcome"] for h in hist_3y]
        wr_3y = outcomes_3y.count("W") / len(outcomes_3y)
    else:
        wr_3y = 0.5

    slpm_3y_list = [h["SlpM"] for h in hist_3y if pd.notna(h["SlpM"])]
    slpm_3y = np.mean(slpm_3y_list) if len(slpm_3y_list) > 0 else slpm

    sapm_3y_list = [h["SApM"] for h in hist_3y if pd.notna(h["SApM"])]
    sapm_3y = np.mean(sapm_3y_list) if len(sapm_3y_list) > 0 else sapm

    td_def_3y_list = [h["TD_Def"] for h in hist_3y if pd.notna(h["TD_Def"])]
    td_def_3y = np.mean(td_def_3y_list) if len(td_def_3y_list) > 0 else td_def

    profile = {
        "reach_cm": reach, "height_cm": height, "age": age,
        "SlpM": slpm, "Str_Acc": str_acc, "SApM": sapm, "Str_Def": str_def,
        "TD_Avg": td_avg, "TD_Acc": td_acc, "TD_Def": td_def, "Sub_Avg": sub_avg,
        # V2
        "elo": elo, "win_streak": win_streak, "loss_streak": loss_streak,
        "win_rate_5": win_rate_5, "ufc_win_rate": ufc_win_rate,
        "ufc_fights": ufc_fights, "rank": rank, "is_ranked": is_ranked,
        # V3
        "wr_3y": wr_3y, "slpm_3y": slpm_3y, "sapm_3y": sapm_3y, "td_def_3y": td_def_3y
    }
    return profile


def predict_matchup_v3(fighter_a, fighter_b, model, raw_df, medians, all_fighters, model_path_used, odds_f1=None, odds_f2=None):
    """Calcule le pronostic V3 et l'analyse financière EV avec récupération auto des cotes (Seuil optimal +20.0%)."""
    name_a = resolve_fighter_name(fighter_a, all_fighters)
    name_b = resolve_fighter_name(fighter_b, all_fighters)

    if not name_a:
        print(f"\n[ERROR] Combattant introuvable : '{fighter_a}'")
        return
    if not name_b:
        print(f"\n[ERROR] Combattant introuvable : '{fighter_b}'")
        return

    if name_a == name_b:
        print("\n[ERROR] Veuillez selectionner deux combattants differents.")
        return

    is_calibrated = "calibrated" in os.path.basename(model_path_used)
    calib_str = " (Modèle Calibré Sigmoïde)" if is_calibrated else ""

    print(f"\n[+] Extraction des donnees V1 + V2 + V3 pour : {fighter_a} vs {fighter_b}")

    # Récupération automatique des cotes si non renseignées manuellement
    odds_source_info = None
    if odds_f1 is None or odds_f2 is None:
        auto_odds = get_odds_for_match(fighter_a, fighter_b)
        if auto_odds:
            odds_f1 = auto_odds["odds_f1"]
            odds_f2 = auto_odds["odds_f2"]
            bkm_name = auto_odds["bookmaker"]
            is_cache = auto_odds["from_cache"]
            age_h = auto_odds.get("cache_age_hours", 0.0)
            source_type = f"Cache local ({age_h:.1f}h)" if is_cache else "API live (The Odds API)"
            odds_source_info = f"Cotes {bkm_name} via {source_type}"

    elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict = compute_fighter_dynamic_states_v3(raw_df)

    profile_a = get_latest_fighter_profile_v3(name_a, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict)
    profile_b = get_latest_fighter_profile_v3(name_b, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict)

    if profile_a is None or profile_b is None:
        print(f"\n[ERROR] Profil historique incomplet pour l'un des combattants. Annulation.")
        return

    delta_dict = {}

    # V1
    for stat in STAT_COLS_V1:
        delta_key = f"delta_{stat}"
        val_a, val_b = profile_a[stat], profile_b[stat]
        delta_dict[delta_key] = (val_a - val_b) if (pd.notna(val_a) and pd.notna(val_b)) else medians.get(delta_key, 0.0)

    # V2
    delta_dict["delta_elo"] = profile_a["elo"] - profile_b["elo"]
    delta_dict["delta_win_streak"] = profile_a["win_streak"] - profile_b["win_streak"]
    delta_dict["delta_loss_streak"] = profile_a["loss_streak"] - profile_b["loss_streak"]
    delta_dict["delta_win_rate_last_5"] = profile_a["win_rate_5"] - profile_b["win_rate_5"]
    delta_dict["delta_ufc_win_rate"] = profile_a["ufc_win_rate"] - profile_b["ufc_win_rate"]
    delta_dict["delta_ufc_fights"] = profile_a["ufc_fights"] - profile_b["ufc_fights"]
    delta_dict["delta_rank"] = profile_b["rank"] - profile_a["rank"]
    delta_dict["is_ranked_f1"] = profile_a["is_ranked"]
    delta_dict["is_ranked_f2"] = profile_b["is_ranked"]

    # V3 (3-year rolling deltas)
    delta_dict["delta_win_rate_3y"] = profile_a["wr_3y"] - profile_b["wr_3y"]
    delta_dict["delta_SlpM_3y"] = (profile_a["slpm_3y"] - profile_b["slpm_3y"]) if (pd.notna(profile_a["slpm_3y"]) and pd.notna(profile_b["slpm_3y"])) else medians.get("delta_SlpM_3y", 0.0)
    delta_dict["delta_SApM_3y"] = (profile_a["sapm_3y"] - profile_b["sapm_3y"]) if (pd.notna(profile_a["sapm_3y"]) and pd.notna(profile_b["sapm_3y"])) else medians.get("delta_SApM_3y", 0.0)
    delta_dict["delta_TD_Def_3y"] = (profile_a["td_def_3y"] - profile_b["td_def_3y"]) if (pd.notna(profile_a["td_def_3y"]) and pd.notna(profile_b["td_def_3y"])) else medians.get("delta_TD_Def_3y", 0.0)

    X_input = pd.DataFrame([delta_dict])[FEATURE_COLS_V3]

    probabilities = model.predict_proba(X_input)[0]
    prob_b_loss, prob_a_win = probabilities[0], probabilities[1]

    pct_a = prob_a_win * 100
    pct_b = prob_b_loss * 100

    display_name_a = fighter_a
    display_name_b = fighter_b

    predicted_winner = display_name_a if pct_a >= 50.0 else display_name_b
    winner_pct = pct_a if pct_a >= 50.0 else pct_b

    base_estimator = model.estimator if hasattr(model, "estimator") else model
    if hasattr(base_estimator, "calibrated_classifiers_"):
        importances = np.mean([c.estimator.feature_importances_ for c in base_estimator.calibrated_classifiers_], axis=0)
    elif hasattr(base_estimator, "feature_importances_"):
        importances = base_estimator.feature_importances_
    else:
        importances = np.ones(len(FEATURE_COLS_V3)) / len(FEATURE_COLS_V3)

    impacts = []
    for idx, col in enumerate(FEATURE_COLS_V3):
        val = delta_dict[col]
        imp = importances[idx]
        impact_score = abs(val) * imp

        favors_a = ((val > 0 and col not in ["delta_SApM", "delta_SApM_3y"]) or (val < 0 and col in ["delta_SApM", "delta_SApM_3y"]))
        if col == "is_ranked_f1":
            favors_a = (val == 1.0)
        elif col == "is_ranked_f2":
            favors_a = (val == 0.0)

        impacts.append({
            "col": col,
            "label": DELTA_LABELS_MAP.get(col, col),
            "delta_value": val,
            "impact_score": impact_score,
            "favors": display_name_a if favors_a else display_name_b
        })

    impacts_sorted = sorted(impacts, key=lambda x: x["impact_score"], reverse=True)[:3]

    print("\n" + "=" * 65)
    print(f"      RESULTAT DU PRONOSTIC UFC V3{calib_str.upper()}")
    print("=" * 65)
    print(f"\n   [Combattant A] : {display_name_a}")
    print(f"   [Combattant B] : {display_name_b}")
    print("\n" + "-" * 65)
    print(f" [VAINQUEUR PREDIT] : {predicted_winner} ({winner_pct:.1f}% de confiance)")
    print("-" * 65)
    print(f"\n [PROBABILITES DE VICTOIRE CALIBREES] :")
    print(f"    * {display_name_a:<25} : {pct_a:.1f}%")
    print(f"    * {display_name_b:<25} : {pct_b:.1f}%")

    print("\n [TOP 3 DES FACTEURS CLES DU COMBAT] :")
    for i, item in enumerate(impacts_sorted, 1):
        sign = "+" if item["delta_value"] > 0 else ""
        print(f"    {i}. {item['label']}")
        print(f"       Delta = {sign}{item['delta_value']:.2f} (Avantage {item['favors']})")

    # DIAGNOSTIC FINANCIER & CALCULE DE L'EV (SEUIL OPTIMAL +20.0%)
    if odds_f1 is not None and odds_f2 is not None and odds_f1 > 1.0 and odds_f2 > 1.0:
        ev_a = (prob_a_win * odds_f1) - 1.0
        ev_b = (prob_b_loss * odds_f2) - 1.0

        print("\n" + "=" * 65)
        print(" 💰 ANALYSE FINANCIÈRE & ESPÉRANCE MATHÉMATIQUE (EV) 💰")
        print("=" * 65)
        if odds_source_info:
            print(f"   [+] Source : {odds_source_info}")
        print(f"    • Cote {display_name_a:<20} : {odds_f1:.2f}  ==>  EV = {ev_a:+.2f} ({ev_a*100:+.1f}%)")
        print(f"    • Cote {display_name_b:<20} : {odds_f2:.2f}  ==>  EV = {ev_b:+.2f} ({ev_b*100:+.1f}%)")

        best_ev = max(ev_a, ev_b)
        best_fighter = display_name_a if ev_a >= ev_b else display_name_b
        best_odds = odds_f1 if ev_a >= ev_b else odds_f2
        best_prob = prob_a_win if ev_a >= ev_b else prob_b_loss

        print("\n" + "-" * 65)

        ev_threshold_optimal = 0.20
        if best_ev > ev_threshold_optimal:
            print(f" 💰 VALUE BET DÉTECTÉ SUR : {best_fighter.upper()}")
            print(f"    -> Avantage Théorique EV : {best_ev * 100:+.1f}% (> +20.0%)")
            print(f"    -> Cote : {best_odds:.2f}")
        else:
            print(" 🚨 PAS DE VALUE BET DÉTECTÉ")
            print("    -> L'espérance mathématique (EV) est insuffisante (<= +20.0%). Aucun pari recommandé.")

    print("=" * 65 + "\n")


def interactive_cli(model, raw_df, medians, all_fighters, model_path_used):
    """Mode interactif."""
    print("=" * 65)
    print("    BIENVENUE SUR L'INTERFACE DE PREDICTION UFC V3")
    print("=" * 65)
    print("Entrez les noms des combattants pour calculer le pronostic V3.")

    try:
        f1 = input("\nNom du Combattant A (ex: Ian Machado Garry) : ").strip()
        f2 = input("Nom du Combattant B (ex: Islam Makhachev)     : ").strip()

        odds_1_str = input("Cote pour Combattant A (ex: 1.85, appuyer Entrée pour auto-détection) : ").strip()
        odds_2_str = input("Cote pour Combattant B (ex: 2.05, appuyer Entrée pour auto-détection) : ").strip()

        o1 = float(odds_1_str) if odds_1_str else None
        o2 = float(odds_2_str) if odds_2_str else None

        if f1 and f2:
            predict_matchup_v3(f1, f2, model, raw_df, medians, all_fighters, model_path_used, odds_f1=o1, odds_f2=o2)
        else:
            print("\n[!] Les deux noms de combattants doivent etre renseignes.")
    except KeyboardInterrupt:
        print("\n\nOperation annulee par l'utilisateur.")


def main():
    parser = argparse.ArgumentParser(description="Prediction V3 de combats UFC via modele XGBoost")
    parser.add_argument("--f1", type=str, help="Nom du Combattant A")
    parser.add_argument("--f2", type=str, help="Nom du Combattant B")
    parser.add_argument("--odds_f1", type=float, help="Cote decimal pour Combattant A (ex: 1.85)")
    parser.add_argument("--odds_f2", type=float, help="Cote decimal pour Combattant B (ex: 2.05)")

    args = parser.parse_args()

    model, raw_df, medians, all_fighters, model_path_used = load_resources_v3()

    if args.f1 and args.f2:
        predict_matchup_v3(
            args.f1, args.f2, model, raw_df, medians, all_fighters, model_path_used,
            odds_f1=args.odds_f1, odds_f2=args.odds_f2
        )
    else:
        interactive_cli(model, raw_df, medians, all_fighters, model_path_used)


if __name__ == "__main__":
    main()
