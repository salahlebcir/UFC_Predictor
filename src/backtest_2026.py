"""
Script de simulation financière et de backtest sur l'année 2026 (Mise Fixe 10 € / Value Bet EV > +20.0%).
Calcule le bilan financier réel sur les combats de 2026.
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

# Paths
PROCESSED_DATA_V3_PATH = os.path.join("data", "processed", "ufc_features_delta_v3.csv")
MODEL_CALIBRATED_PATH = os.path.join("models", "ufc_xgboost_model_v3_calibrated.pkl")
MODEL_V3_PATH = os.path.join("models", "ufc_xgboost_model_v3.pkl")
RESULTS_2026_OUTPUT_PATH = os.path.join("data", "backtest_2026_results.json")


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


def run_backtest_2026():
    print("=" * 85)
    print(" 🥊 SIMULATION FINANCIÈRE DÉDIÉE ANNÉE 2026 (MISE FIXE 10 € - SEUIL EV > +20.0%) 🥊")
    print("=" * 85)

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

    # Filtrage STRICT sur l'année 2026
    df_2026 = df_full[df_full["event_date"] >= "2026-01-01"].copy().reset_index(drop=True)

    # Filtrer STRICTEMENT les combats avec cotes valides
    valid_2026_df = df_2026[
        df_2026["f_1_odds"].notna() &
        df_2026["f_2_odds"].notna() &
        (df_2026["f_1_odds"] > 1.0) &
        (df_2026["f_2_odds"] > 1.0)
    ].copy().reset_index(drop=True)

    total_2026_fights = len(valid_2026_df)
    print(f"   -> Combats UFC analysés en 2026 avec cotes : {total_2026_fights}")

    feature_cols = [col for col in valid_2026_df.columns if col.startswith("delta_") or col.startswith("is_ranked_")]
    X_2026 = valid_2026_df[feature_cols]
    y_2026 = valid_2026_df["Y"].values

    probs = model.predict_proba(X_2026)
    p_f1 = probs[:, 1]
    p_f2 = probs[:, 0]

    odds_f1 = valid_2026_df["f_1_odds"].values
    odds_f2 = valid_2026_df["f_2_odds"].values
    f1_names = valid_2026_df["f_1_name"].values
    f2_names = valid_2026_df["f_2_name"].values
    dates_2026 = valid_2026_df["event_date"].dt.strftime("%Y-%m-%d").values

    ev_threshold = 0.20  # +20.0%
    flat_stake = 10.0  # 10 € par pari

    initial_bankroll = 1000.0
    bankroll = initial_bankroll
    bankroll_history = [bankroll]

    bets_count = 0
    wins_count = 0
    total_wagered = 0.0
    gross_payout = 0.0

    bets_records = []

    for i in range(total_2026_fights):
        p1, p2 = p_f1[i], p_f2[i]
        o1, o2 = odds_f1[i], odds_f2[i]
        actual_y = y_2026[i]

        ev1 = (p1 * o1) - 1.0
        ev2 = (p2 * o2) - 1.0

        bet_choice = None

        if ev1 > ev_threshold and ev1 >= ev2:
            bet_choice = 1
            bet_prob = p1
            bet_odds = o1
            bet_ev = ev1
            bet_won = (actual_y == 1)
            fighter_bet = f1_names[i]
        elif ev2 > ev_threshold and ev2 > ev1:
            bet_choice = 2
            bet_prob = p2
            bet_odds = o2
            bet_ev = ev2
            bet_won = (actual_y == 0)
            fighter_bet = f2_names[i]

        if bet_choice is not None:
            bets_count += 1
            total_wagered += flat_stake

            if bet_won:
                wins_count += 1
                payout = flat_stake * bet_odds
                gross_payout += payout
                bankroll += (payout - flat_stake)
            else:
                bankroll -= flat_stake

            bankroll_history.append(bankroll)

            bets_records.append({
                "date": dates_2026[i],
                "fighter": fighter_bet,
                "odds": float(bet_odds),
                "prob": float(bet_prob),
                "ev": float(bet_ev),
                "won": bool(bet_won),
                "bankroll": float(bankroll)
            })

    net_profit = bankroll - initial_bankroll
    roi = (net_profit / total_wagered * 100.0) if total_wagered > 0 else 0.0
    win_rate = (wins_count / bets_count * 100.0) if bets_count > 0 else 0.0
    pct_bets_2026 = (bets_count / total_2026_fights * 100.0) if total_2026_fights > 0 else 0.0
    max_dd = calculate_max_drawdown(bankroll_history)

    print("\n" + "=" * 85)
    print(" 📊 RAPPORT FINANCIER SPÉCIFIQUE ANNÉE 2026 (SEUIL EV > +20.0%) 📊")
    print("=" * 85)

    print(f"\n   • Total de combats analysés en 2026      : {total_2026_fights}")
    print(f"   • Value Bets détectés & pris (EV > +20%) : {bets_count} ({pct_bets_2026:.1f}% des combats)")
    print(f"   • Taux de Réussite Réel (Win Rate)       : {win_rate:.2f}% ({wins_count} victoires / {bets_count} paris)")

    print("\n" + "-" * 85)
    print(" 💵 BILAN COMPTABLE DE L'ANNÉE 2026 (MISE FIXE 10.00 €)")
    print("-" * 85)
    print(f"    • Total des Mises Engagées  : {total_wagered:.2f} €")
    print(f"    • Gains Bruts Encaisssés    : {gross_payout:.2f} €")
    print(f"    • Profit Net Total (Bénéfice): {net_profit:+.2f} €")
    print(f"    • ROI 2026 (%)              : {roi:+.2f} %")
    print(f"    • Max Drawdown 2026 (%)     : {max_dd:.2f} %")
    print("=" * 85)

    # Sauvegarde des résultats JSON
    summary_2026 = {
        "year": 2026,
        "model_used": target_model_path,
        "stake_per_bet": flat_stake,
        "ev_threshold": ev_threshold,
        "total_fights": total_2026_fights,
        "value_bets_count": bets_count,
        "win_rate_pct": float(win_rate),
        "total_wagered": float(total_wagered),
        "gross_payout": float(gross_payout),
        "net_profit": float(net_profit),
        "roi_pct": float(roi),
        "max_drawdown_pct": float(max_dd),
        "bets": bets_records
    }

    os.makedirs(os.path.dirname(RESULTS_2026_OUTPUT_PATH), exist_ok=True)
    with open(RESULTS_2026_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary_2026, f, indent=4)
    print(f"\n   [+] Bilan financier 2026 sauvegardé dans : {RESULTS_2026_OUTPUT_PATH}\n")


if __name__ == "__main__":
    run_backtest_2026()
