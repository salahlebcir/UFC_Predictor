"""
Script de backtest financier sur cotes réelles / réelles de marché.
Évalue le Retour sur Investissement (ROI) et l'Espérance Mathématique (EV)
du modèle UFC V3 Calibré sur le jeu de test non vu (2015-2026, 20% test set, random_state=42).

Simule 2 stratégies de gestion de bankroll (Bankroll Initiale = 1 000 €) :
1. Mise Fixe (Flat Betting 20 €)
2. Kelly Fractionnel (Kelly 1/4)
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


def run_financial_backtest():
    print("=" * 80)
    print(" 💰 BACKTEST FINANCIER SUR COTES HISTORIQUES (MODÈLE V3 CALIBRÉ) 💰")
    print("=" * 80)

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
    print(f"   -> Dataset filtré 2015–2026 : {len(df)} combats")

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

    print(f"   -> Jeu de test isolé (20% non vu) : {len(test_df)} combats")
    print(f"   -> Combats avec cotes réelles exploitables : {len(valid_test_df)} combats")

    X_test_valid = valid_test_df[feature_cols]
    y_test_valid = valid_test_df["Y"].values

    # Prédictions calibrées
    probs = model.predict_proba(X_test_valid)
    p_f1 = probs[:, 1]
    p_f2 = probs[:, 0]

    odds_f1 = valid_test_df["f_1_odds"].values
    odds_f2 = valid_test_df["f_2_odds"].values
    f1_names = valid_test_df["f_1_name"].values
    f2_names = valid_test_df["f_2_name"].values
    event_dates = valid_test_df["event_date"].dt.strftime("%Y-%m-%d").values

    # SIMULATION DE STRATÉGIE FINANCIÈRE
    initial_bankroll = 1000.0

    # 1. Flat Betting (20 € fixe par Value Bet)
    flat_stake = 20.0
    flat_bankroll = initial_bankroll
    flat_history = [flat_bankroll]
    flat_total_wagered = 0.0
    flat_bets_count = 0
    flat_wins_count = 0

    # 2. Kelly 1/4
    kelly_bankroll = initial_bankroll
    kelly_history = [kelly_bankroll]
    kelly_total_wagered = 0.0
    kelly_bets_count = 0
    kelly_wins_count = 0

    value_bets_records = []

    for i in range(len(valid_test_df)):
        p1, p2 = p_f1[i], p_f2[i]
        o1, o2 = odds_f1[i], odds_f2[i]
        actual_y = y_test_valid[i]  # 1 = F1 gagne, 0 = F2 gagne

        # Calcul Espérance Mathématique EV = (P * Cote) - 1
        ev1 = (p1 * o1) - 1.0
        ev2 = (p2 * o2) - 1.0

        bet_choice = None

        # Value Bet condition: EV > 0.05 (+5% d'avantage théorique)
        if ev1 > 0.05 and ev1 >= ev2:
            bet_choice = 1
            bet_prob = p1
            bet_odds = o1
            bet_ev = ev1
            bet_won = (actual_y == 1)
            fighter_bet = f1_names[i]
        elif ev2 > 0.05 and ev2 > ev1:
            bet_choice = 2
            bet_prob = p2
            bet_odds = o2
            bet_ev = ev2
            bet_won = (actual_y == 0)
            fighter_bet = f2_names[i]

        if bet_choice is not None:
            # A. FLAT BETTING
            flat_bets_count += 1
            flat_total_wagered += flat_stake

            if bet_won:
                flat_wins_count += 1
                flat_bankroll += flat_stake * (bet_odds - 1.0)
            else:
                flat_bankroll -= flat_stake

            flat_history.append(flat_bankroll)

            # B. KELLY FRACTIONNEL (KELLY 1/4)
            kelly_bets_count += 1
            net_odds = bet_odds - 1.0
            full_kelly_f = (bet_prob * bet_odds - 1.0) / net_odds if net_odds > 0 else 0.0
            kelly_fraction = 0.25 * full_kelly_f

            # Capping de sécurité à 5% max de la bankroll courante
            kelly_fraction = min(max(kelly_fraction, 0.0), 0.05)
            kelly_stake = kelly_bankroll * kelly_fraction

            if kelly_stake > 0.5:
                kelly_total_wagered += kelly_stake
                if bet_won:
                    kelly_wins_count += 1
                    kelly_bankroll += kelly_stake * (bet_odds - 1.0)
                else:
                    kelly_bankroll -= kelly_stake

            kelly_history.append(kelly_bankroll)

            value_bets_records.append({
                "date": event_dates[i],
                "fighter": fighter_bet,
                "odds": bet_odds,
                "prob": bet_prob,
                "ev": bet_ev,
                "won": bet_won,
                "flat_bankroll": flat_bankroll,
                "kelly_bankroll": kelly_bankroll
            })

    # Calcul des métriques financières
    flat_profit = flat_bankroll - initial_bankroll
    flat_roi = (flat_profit / flat_total_wagered * 100.0) if flat_total_wagered > 0 else 0.0
    flat_win_rate = (flat_wins_count / flat_bets_count * 100.0) if flat_bets_count > 0 else 0.0
    flat_max_dd = calculate_max_drawdown(flat_history)

    kelly_profit = kelly_bankroll - initial_bankroll
    kelly_roi = (kelly_profit / kelly_total_wagered * 100.0) if kelly_total_wagered > 0 else 0.0
    kelly_win_rate = (kelly_wins_count / kelly_bets_count * 100.0) if kelly_bets_count > 0 else 0.0
    kelly_max_dd = calculate_max_drawdown(kelly_history)

    print("\n" + "=" * 80)
    print(" 📊 RÉSULTATS DU BACKTEST FINANCIER (MODÈLE V3 CALIBRÉ) 📊")
    print("=" * 80)

    print(f"\n   • Combats analysés avec cotes réelles : {len(valid_test_df)}")
    print(f"   • Value Bets détectés (EV > +5%)     : {flat_bets_count} ({flat_bets_count / len(valid_test_df) * 100:.1f}% des combats)")
    print(f"   • Taux de Réussite sur Value Bets    : {flat_win_rate:.2f}% ({flat_wins_count} victoires / {flat_bets_count} paris)")

    print("\n" + "-" * 80)
    print(" 💵 STRATÉGIE 1 : MISE FIXE (FLAT BETTING - 20 € / PARI)")
    print("-" * 80)
    print(f"    • Capital Initial        : {initial_bankroll:.2f} €")
    print(f"    • Capital Final          : {flat_bankroll:.2f} €")
    print(f"    • Total Misé             : {flat_total_wagered:.2f} €")
    print(f"    • Profit Net Total       : {flat_profit:+.2f} €")
    print(f"    • ROI (Retour S. Invest) : {flat_roi:+.2f} %")
    print(f"    • Max Drawdown (Pire DD) : {flat_max_dd:.2f} %")

    print("\n" + "-" * 80)
    print(" 🚀 STRATÉGIE 2 : KELLY FRACTIONNEL (KELLY 1/4)")
    print("-" * 80)
    print(f"    • Capital Initial        : {initial_bankroll:.2f} €")
    print(f"    • Capital Final          : {kelly_bankroll:.2f} €")
    print(f"    • Total Misé             : {kelly_total_wagered:.2f} €")
    print(f"    • Profit Net Total       : {kelly_profit:+.2f} €")
    print(f"    • ROI (Retour S. Invest) : {kelly_roi:+.2f} %")
    print(f"    • Max Drawdown (Pire DD) : {kelly_max_dd:.2f} %")
    print("=" * 80 + "\n")

    # Enregistrement des résultats de backtest
    backtest_summary = {
        "model_used": target_model_path,
        "total_test_fights": len(valid_test_df),
        "value_bets_count": flat_bets_count,
        "win_rate": float(flat_win_rate),
        "flat_betting": {
            "initial_bankroll": initial_bankroll,
            "final_bankroll": float(flat_bankroll),
            "total_wagered": float(flat_total_wagered),
            "profit": float(flat_profit),
            "roi_pct": float(flat_roi),
            "max_drawdown_pct": float(flat_max_dd)
        },
        "kelly_quarter": {
            "initial_bankroll": initial_bankroll,
            "final_bankroll": float(kelly_bankroll),
            "total_wagered": float(kelly_total_wagered),
            "profit": float(kelly_profit),
            "roi_pct": float(kelly_roi),
            "max_drawdown_pct": float(kelly_max_dd)
        }
    }

    out_json = os.path.join("models", "backtest_financial_results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(backtest_summary, f, indent=4)
    print(f"   [+] Bilan financier sauvegardé dans : {out_json}\n")


if __name__ == "__main__":
    run_financial_backtest()
