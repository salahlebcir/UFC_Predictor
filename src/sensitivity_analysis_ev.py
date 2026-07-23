"""
Script d'analyse de sélectivité et de sensibilité des seuils d'Espérance Mathématique (EV).
Évalue l'impact du seuil d'EV (de 0.0% à 20.0%) sur le ROI, le Profit Net, le Win Rate et le Max Drawdown.
Traitement 100% local sur data/processed/ufc_features_delta_v3.csv (0 appel API).
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np

# System stdout encoding fallback for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sklearn.model_selection import train_test_split

# Paths
PROCESSED_DATA_V3_PATH = os.path.join("data", "processed", "ufc_features_delta_v3.csv")
MODEL_CALIBRATED_PATH = os.path.join("models", "ufc_xgboost_model_v3_calibrated.pkl")
MODEL_V3_PATH = os.path.join("models", "ufc_xgboost_model_v3.pkl")
RESULTS_OUTPUT_PATH = os.path.join("data", "ev_sensitivity_results.json")


def calculate_max_drawdown(bankroll_history):
    """Calcule le Maximum Drawdown (en %) d'une courbe de bankroll."""
    peak = bankroll_history[0]
    max_dd = 0.0
    for val in bankroll_history:
        if val > peak:
            peak = val
        dd = (peak - val) / peak
        if dd > max_dd:
            max_dd = dd
    return float(max_dd * 100.0)


def run_sensitivity_analysis():
    print("=" * 110)
    print(" 📊 ANALYSE DE SÉLECTIVITÉ DES SEUILS D'ESPÉRANCE MATHÉMATIQUE (EV) 📊")
    print("=" * 110)

    if not os.path.exists(PROCESSED_DATA_V3_PATH):
        raise FileNotFoundError(f"Le fichier {PROCESSED_DATA_V3_PATH} est introuvable. Exécutez d'abord src/data_prep.py.")

    target_model_path = MODEL_CALIBRATED_PATH if os.path.exists(MODEL_CALIBRATED_PATH) else MODEL_V3_PATH
    if not os.path.exists(target_model_path):
        raise FileNotFoundError(f"Le modèle {target_model_path} est introuvable.")

    model = joblib.load(target_model_path)
    model_name_str = "V3 Calibré Sigmoïde" if "calibrated" in target_model_path else "V3 Brut"
    print(f"   -> Modèle chargé : {model_name_str} ({target_model_path})")

    df_full = pd.read_csv(PROCESSED_DATA_V3_PATH)
    df_full["event_date"] = pd.to_datetime(df_full["event_date"], errors="coerce")

    # Filtrage 2015-2026
    df = df_full[df_full["event_date"] >= "2015-01-01"].copy().reset_index(drop=True)
    feature_cols = [col for col in df.columns if col.startswith("delta_") or col.startswith("is_ranked_")]

    # Split Train (80%) / Test (20%) avec random_state=42
    train_df, test_df = train_test_split(
        df, test_size=0.20, random_state=42, stratify=df["Y"]
    )
    test_df = test_df.reset_index(drop=True)

    # Filtrer STRICTEMENT les combats avec cotes valides
    valid_test_df = test_df[
        test_df["f_1_odds"].notna() &
        test_df["f_2_odds"].notna() &
        (test_df["f_1_odds"] > 1.0) &
        (test_df["f_2_odds"] > 1.0)
    ].copy().reset_index(drop=True)

    total_test_fights = len(valid_test_df)
    print(f"   -> Dataset test 2015-2026 isolé : {total_test_fights} combats avec cotes historiques")

    X_test_valid = valid_test_df[feature_cols]
    y_test_valid = valid_test_df["Y"].values

    probs = model.predict_proba(X_test_valid)
    p_f1 = probs[:, 1]
    p_f2 = probs[:, 0]

    odds_f1 = valid_test_df["f_1_odds"].values
    odds_f2 = valid_test_df["f_2_odds"].values

    ev_thresholds = [0.00, 0.025, 0.05, 0.075, 0.10, 0.125, 0.15, 0.20]
    results = []

    initial_bankroll = 1000.0
    flat_stake = 20.0

    for thresh in ev_thresholds:
        bankroll = initial_bankroll
        history = [bankroll]
        total_wagered = 0.0
        bets_count = 0
        wins_count = 0

        for i in range(total_test_fights):
            p1, p2 = p_f1[i], p_f2[i]
            o1, o2 = odds_f1[i], odds_f2[i]
            actual_y = y_test_valid[i]

            ev1 = (p1 * o1) - 1.0
            ev2 = (p2 * o2) - 1.0

            bet_choice = None

            if ev1 > thresh and ev1 >= ev2:
                bet_choice = 1
                bet_odds = o1
                bet_won = (actual_y == 1)
            elif ev2 > thresh and ev2 > ev1:
                bet_choice = 2
                bet_odds = o2
                bet_won = (actual_y == 0)

            if bet_choice is not None:
                bets_count += 1
                total_wagered += flat_stake

                if bet_won:
                    wins_count += 1
                    bankroll += flat_stake * (bet_odds - 1.0)
                else:
                    bankroll -= flat_stake

                history.append(bankroll)

        profit = bankroll - initial_bankroll
        roi = (profit / total_wagered * 100.0) if total_wagered > 0 else 0.0
        win_rate = (wins_count / bets_count * 100.0) if bets_count > 0 else 0.0
        pct_bets = (bets_count / total_test_fights * 100.0)
        max_dd = calculate_max_drawdown(history)

        results.append({
            "threshold": thresh,
            "threshold_pct": f"+{thresh * 100:.1f}%",
            "bets_count": bets_count,
            "pct_bets": pct_bets,
            "win_rate": win_rate,
            "total_wagered": total_wagered,
            "profit": profit,
            "roi": roi,
            "max_drawdown": max_dd
        })

    # Affichage du tableau récapitulatif
    print("\n" + "=" * 110)
    print(" 📈 MATRICE COMPARATIVE DE SÉLECTIVITÉ EV (FLAT BETTING 20 €) 📈")
    print("=" * 110)
    header = f"| {'Seuil EV':<10} | {'Paris Pris (Nb / %)':<21} | {'Win Rate (%)':<14} | {'Total Misé (€)':<16} | {'Profit Net (€)':<16} | {'ROI (%)':<10} | {'Max Drawdown (%)':<18} |"
    print(header)
    print("|" + "-" * 12 + "|" + "-" * 23 + "|" + "-" * 16 + "|" + "-" * 18 + "|" + "-" * 18 + "|" + "-" * 12 + "|" + "-" * 20 + "|")

    best_roi_res = max(results, key=lambda x: x["roi"])

    # Score de compromis (Profit Net élevé avec Drawdown faible)
    best_balance_res = max(results, key=lambda x: (x["profit"] / (x["max_drawdown"] + 1.0)))

    for r in results:
        star_roi = "  <-- MAX ROI" if r["threshold"] == best_roi_res["threshold"] else ""
        star_bal = "  <-- MEILLEUR COMPROMIS" if r["threshold"] == best_balance_res["threshold"] and r["threshold"] != best_roi_res["threshold"] else ""
        star = star_roi or star_bal

        bets_str = f"{r['bets_count']} ({r['pct_bets']:.1f}%)"
        row_str = f"| {r['threshold_pct']:<10} | {bets_str:<21} | {r['win_rate']:<14.2f}% | {r['total_wagered']:<16.2f} € | {r['profit']:<+16.2f} € | {r['roi']:<+10.2f}% | {r['max_drawdown']:<18.2f}% |{star}"
        print(row_str)

    print("=" * 110)

    print("\n 💡 CONCLUSION & SYNTHÈSE EXPLICATIVE :")
    print(f"   • Seuil maximisant le ROI (%)                     : Seuil {best_roi_res['threshold_pct']} avec un ROI de {best_roi_res['roi']:+.2f}% (Win Rate: {best_roi_res['win_rate']:.2f}%)")
    print(f"   • Seuil optimisant le compromis Profit / Sécurité : Seuil {best_balance_res['threshold_pct']} (Profit: {best_balance_res['profit']:+.2f} €, Max DD: {best_balance_res['max_drawdown']:.2f}%)")

    # Enregistrement des résultats JSON
    os.makedirs(os.path.dirname(RESULTS_OUTPUT_PATH), exist_ok=True)
    summary_to_save = {
        "model_used": target_model_path,
        "total_test_fights": total_test_fights,
        "best_roi_threshold": best_roi_res["threshold"],
        "best_balance_threshold": best_balance_res["threshold"],
        "grid_results": results
    }

    with open(RESULTS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary_to_save, f, indent=4)
    print(f"\n   [+] Synthèse de sélectivité sauvegardée dans : {RESULTS_OUTPUT_PATH}\n")


if __name__ == "__main__":
    run_sensitivity_analysis()
