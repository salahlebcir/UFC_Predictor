"""
Script de préparation et de nettoyage des données UFC - MODULE V3.
Calcule chronologiquement (1994 -> 2026) l'état dynamique (Elo, Forme, Palmarès, Rang)
et les 4 fenêtres glissantes sur 3 ans (36 mois) :
- delta_win_rate_3y
- delta_SlpM_3y
- delta_SApM_3y
- delta_TD_Def_3y

Génère/Conserve également les cotes de marché réelles/réalistes (f_1_odds, f_2_odds)
avec surmarge bookmaker de 5% pour le backtest financier.
Filtre ensuite le dataset pour l'entraînement Machine Learning sur l'Ère Moderne (2010 -> 2026),
applique la permutation 50/50 anti-leakage, impute les médianes et sauvegarde ufc_features_delta_v3.csv.
"""

import os
import json
import collections
import numpy as np
import pandas as pd

# Paths
RAW_DATA_PATH = os.path.join("data", "raw", "UFC_full_data_silver_v2.csv")
PROCESSED_DATA_V3_PATH = os.path.join("data", "processed", "ufc_features_delta_v3.csv")
MEDIANS_V3_PATH = os.path.join("data", "processed", "feature_medians_v3.json")


def load_and_preprocess_v3():
    print("=" * 65)
    print("1. Chargement du dataset brut pour le Module V3 (Ère Moderne + Fenêtres 3 ans)...")
    if not os.path.exists(RAW_DATA_PATH):
        raise FileNotFoundError(f"Le fichier brut {RAW_DATA_PATH} est introuvable.")

    df = pd.read_csv(RAW_DATA_PATH, low_memory=False)
    print(f"   -> Nombre total de lignes chargées : {len(df)}")

    # 2. Filtrage et tri chronologique strict (1994 -> 2026)
    print("\n2. Filtrage et tri chronologique (1994 -> 2026)...")
    df = df.dropna(subset=["winner"]).copy()
    df = df[df["winner"].isin(df["f_1_name"]) | df["winner"].isin(df["f_2_name"])].copy()

    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    df = df.sort_values(by="event_date", ascending=True).reset_index(drop=True)
    print(f"   -> Combats valides triés chronologiquement : {len(df)}")

    # Dates de naissance & calcul d'âge
    df["f_1_fighter_dob"] = pd.to_datetime(df["f_1_fighter_dob"], errors="coerce")
    df["f_2_fighter_dob"] = pd.to_datetime(df["f_2_fighter_dob"], errors="coerce")
    df["age_f1"] = (df["event_date"] - df["f_1_fighter_dob"]).dt.days / 365.25
    df["age_f2"] = (df["event_date"] - df["f_2_fighter_dob"]).dt.days / 365.25

    # Colonnes statistiques V1
    v1_stat_cols = [
        "reach_cm", "height_cm", "age",
        "SlpM", "Str_Acc", "SApM", "Str_Def",
        "TD_Avg", "TD_Acc", "TD_Def", "Sub_Avg"
    ]

    col_mapping_f1 = {
        "reach_cm": "f_1_fighter_reach_cm",
        "height_cm": "f_1_fighter_height_cm",
        "age": "age_f1",
        "SlpM": "f_1_fighter_SlpM",
        "Str_Acc": "f_1_fighter_Str_Acc",
        "SApM": "f_1_fighter_SApM",
        "Str_Def": "f_1_fighter_Str_Def",
        "TD_Avg": "f_1_fighter_TD_Avg",
        "TD_Acc": "f_1_fighter_TD_Acc",
        "TD_Def": "f_1_fighter_TD_Def",
        "Sub_Avg": "f_1_fighter_Sub_Avg"
    }

    col_mapping_f2 = {
        "reach_cm": "f_2_fighter_reach_cm",
        "height_cm": "f_2_fighter_height_cm",
        "age": "age_f2",
        "SlpM": "f_2_fighter_SlpM",
        "Str_Acc": "f_2_fighter_Str_Acc",
        "SApM": "f_2_fighter_SApM",
        "Str_Def": "f_2_fighter_Str_Def",
        "TD_Avg": "f_2_fighter_TD_Avg",
        "TD_Acc": "f_2_fighter_TD_Acc",
        "TD_Def": "f_2_fighter_TD_Def",
        "Sub_Avg": "f_2_fighter_Sub_Avg"
    }

    for raw_col in list(col_mapping_f1.values()) + list(col_mapping_f2.values()):
        if raw_col in df.columns:
            df[raw_col] = pd.to_numeric(df[raw_col], errors="coerce")

    # Suivi chronologique de l'état des combattants
    elo_dict = collections.defaultdict(lambda: 1500.0)
    history_dict = collections.defaultdict(list)
    win_streak_dict = collections.defaultdict(int)
    loss_streak_dict = collections.defaultdict(int)

    print("\n3. Calcul des métriques chronologiques, fenêtres 3 ans et cotes de marché...")

    np.random.seed(42)
    swap_mask_all = np.random.rand(len(df)) >= 0.5

    processed_rows = []
    cutoff_date = pd.Timestamp("2010-01-01")

    for idx, row in df.iterrows():
        f1 = row["f_1_name"]
        f2 = row["f_2_name"]
        winner = row["winner"]
        event_dt = row["event_date"]
        is_swapped = swap_mask_all[idx]

        # --- A. CALCUL DES CARACTÉRISTIQUES DYNAMIQUES ET FENÊTRES GLISSANTES (PRE-FIGHT) ---
        elo_f1 = elo_dict[f1]
        elo_f2 = elo_dict[f2]
        delta_elo_raw = elo_f1 - elo_f2

        win_streak_f1 = win_streak_dict[f1]
        win_streak_f2 = win_streak_dict[f2]
        delta_win_streak_raw = win_streak_f1 - win_streak_f2

        loss_streak_f1 = loss_streak_dict[f1]
        loss_streak_f2 = loss_streak_dict[f2]
        delta_loss_streak_raw = loss_streak_f1 - loss_streak_f2

        hist_f1 = history_dict[f1]
        hist_f2 = history_dict[f2]

        last5_f1 = [h["outcome"] for h in hist_f1[-5:]] if len(hist_f1) > 0 else []
        last5_f2 = [h["outcome"] for h in hist_f2[-5:]] if len(hist_f2) > 0 else []
        win_rate_5_f1 = last5_f1.count("W") / len(last5_f1) if len(last5_f1) > 0 else 0.5
        win_rate_5_f2 = last5_f2.count("W") / len(last5_f2) if len(last5_f2) > 0 else 0.5
        delta_win_rate_last_5_raw = win_rate_5_f1 - win_rate_5_f2

        ufc_fights_f1 = len(hist_f1)
        ufc_fights_f2 = len(hist_f2)
        delta_ufc_fights_raw = ufc_fights_f1 - ufc_fights_f2

        all_outcomes_f1 = [h["outcome"] for h in hist_f1]
        all_outcomes_f2 = [h["outcome"] for h in hist_f2]
        ufc_win_rate_f1 = all_outcomes_f1.count("W") / ufc_fights_f1 if ufc_fights_f1 > 0 else 0.5
        ufc_win_rate_f2 = all_outcomes_f2.count("W") / ufc_fights_f2 if ufc_fights_f2 > 0 else 0.5
        delta_ufc_win_rate_raw = ufc_win_rate_f1 - ufc_win_rate_f2

        raw_r1 = pd.to_numeric(row.get("f_1_ranking"), errors="coerce")
        raw_r2 = pd.to_numeric(row.get("f_2_ranking"), errors="coerce")
        r1 = raw_r1 if (pd.notna(raw_r1) and 1 <= raw_r1 <= 15) else 20.0
        r2 = raw_r2 if (pd.notna(raw_r2) and 1 <= raw_r2 <= 15) else 20.0
        delta_rank_raw = r2 - r1
        is_ranked_f1_raw = 1.0 if r1 <= 15 else 0.0
        is_ranked_f2_raw = 1.0 if r2 <= 15 else 0.0

        # --- FENÊTRES GLISSANTES SUR 3 ANS (36 MOIS) PRE-FIGHT ---
        three_years_ago = event_dt - pd.DateOffset(years=3)

        hist_3y_f1 = [h for h in hist_f1 if h["date"] >= three_years_ago]
        hist_3y_f2 = [h for h in hist_f2 if h["date"] >= three_years_ago]

        wr_3y_f1 = (hist_3y_f1.count("W") / len(hist_3y_f1)) if len(hist_3y_f1) > 0 else 0.5
        wr_3y_f2 = (hist_3y_f2.count("W") / len(hist_3y_f2)) if len(hist_3y_f2) > 0 else 0.5
        delta_win_rate_3y_raw = wr_3y_f1 - wr_3y_f2

        slpm_3y_list_f1 = [h["SlpM"] for h in hist_3y_f1 if pd.notna(h["SlpM"])]
        slpm_3y_list_f2 = [h["SlpM"] for h in hist_3y_f2 if pd.notna(h["SlpM"])]
        mean_slpm_3y_f1 = np.mean(slpm_3y_list_f1) if len(slpm_3y_list_f1) > 0 else np.nan
        mean_slpm_3y_f2 = np.mean(slpm_3y_list_f2) if len(slpm_3y_list_f2) > 0 else np.nan
        delta_SlpM_3y_raw = (mean_slpm_3y_f1 - mean_slpm_3y_f2) if (pd.notna(mean_slpm_3y_f1) and pd.notna(mean_slpm_3y_f2)) else np.nan

        sapm_3y_list_f1 = [h["SApM"] for h in hist_3y_f1 if pd.notna(h["SApM"])]
        sapm_3y_list_f2 = [h["SApM"] for h in hist_3y_f2 if pd.notna(h["SApM"])]
        mean_sapm_3y_f1 = np.mean(sapm_3y_list_f1) if len(sapm_3y_list_f1) > 0 else np.nan
        mean_sapm_3y_f2 = np.mean(sapm_3y_list_f2) if len(sapm_3y_list_f2) > 0 else np.nan
        delta_SApM_3y_raw = (mean_sapm_3y_f1 - mean_sapm_3y_f2) if (pd.notna(mean_sapm_3y_f1) and pd.notna(mean_sapm_3y_f2)) else np.nan

        td_def_3y_list_f1 = [h["TD_Def"] for h in hist_3y_f1 if pd.notna(h["TD_Def"])]
        td_def_3y_list_f2 = [h["TD_Def"] for h in hist_3y_f2 if pd.notna(h["TD_Def"])]
        mean_td_def_3y_f1 = np.mean(td_def_3y_list_f1) if len(td_def_3y_list_f1) > 0 else np.nan
        mean_td_def_3y_f2 = np.mean(td_def_3y_list_f2) if len(td_def_3y_list_f2) > 0 else np.nan
        delta_TD_Def_3y_raw = (mean_td_def_3y_f1 - mean_td_def_3y_f2) if (pd.notna(mean_td_def_3y_f1) and pd.notna(mean_td_def_3y_f2)) else np.nan

        # --- B. GESTION DES COTES DE MARCHÉ RÉELLES / RÉALISTES ---
        raw_odds_1 = pd.to_numeric(row.get("f_1_odds"), errors="coerce")
        raw_odds_2 = pd.to_numeric(row.get("f_2_odds"), errors="coerce")

        if pd.notna(raw_odds_1) and pd.notna(raw_odds_2) and raw_odds_1 > 1.0 and raw_odds_2 > 1.0:
            odds_f1_val = float(raw_odds_1)
            odds_f2_val = float(raw_odds_2)
        else:
            # Génération de cotes réalistes basées sur la probabilité de marché (Elo + Rang + 5% de surmarge bookmaker)
            p1_market_base = 1.0 / (1.0 + 10.0 ** (-delta_elo_raw / 400.0))
            # Ajustement avec le rang
            if r1 <= 15 or r2 <= 15:
                p1_market_base += (r2 - r1) * 0.015
            p1_market_base = float(np.clip(p1_market_base, 0.12, 0.88))
            p2_market_base = 1.0 - p1_market_base

            # Bruit de marché (+- 4% de divergence réelle)
            np.random.seed((idx * 17) % 100000)
            noise = float(np.random.normal(0, 0.03))
            p1_final = float(np.clip(p1_market_base + noise, 0.10, 0.90))
            p2_final = 1.0 - p1_final

            # 5% de surmarge (vigorish / bookmaker margin = 1.05)
            margin = 1.05
            odds_f1_val = round(1.0 / (p1_final * margin), 2)
            odds_f2_val = round(1.0 / (p2_final * margin), 2)

        # --- C. CALCUL DES CARACTÉRISTIQUES V1 ---
        stats_v1_f1 = {stat: row[col_mapping_f1[stat]] for stat in v1_stat_cols}
        stats_v1_f2 = {stat: row[col_mapping_f2[stat]] for stat in v1_stat_cols}

        deltas_v1_raw = {}
        for stat in v1_stat_cols:
            val1 = stats_v1_f1[stat]
            val2 = stats_v1_f2[stat]
            if pd.notna(val1) and pd.notna(val2):
                deltas_v1_raw[f"delta_{stat}"] = val1 - val2
            else:
                deltas_v1_raw[f"delta_{stat}"] = np.nan

        # --- D. MISE À JOUR POST-COMBAT DE L'HISTORIQUE ---
        f1_won = (winner == f1)

        S1 = 1.0 if f1_won else 0.0
        S2 = 0.0 if f1_won else 1.0

        E1 = 1.0 / (1.0 + 10.0 ** ((elo_f2 - elo_f1) / 400.0))
        E2 = 1.0 - E1

        elo_dict[f1] += 32.0 * (S1 - E1)
        elo_dict[f2] += 32.0 * (S2 - E2)

        f1_slpm = stats_v1_f1["SlpM"]
        f1_sapm = stats_v1_f1["SApM"]
        f1_td_def = stats_v1_f1["TD_Def"]

        f2_slpm = stats_v1_f2["SlpM"]
        f2_sapm = stats_v1_f2["SApM"]
        f2_td_def = stats_v1_f2["TD_Def"]

        history_dict[f1].append({
            "date": event_dt, "outcome": "W" if f1_won else "L",
            "SlpM": f1_slpm, "SApM": f1_sapm, "TD_Def": f1_td_def
        })
        history_dict[f2].append({
            "date": event_dt, "outcome": "L" if f1_won else "W",
            "SlpM": f2_slpm, "SApM": f2_sapm, "TD_Def": f2_td_def
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

        # --- E. FILTRAGE PÉRIODE ML (2010 -> 2026) ---
        if pd.notna(event_dt) and event_dt >= cutoff_date:
            if not is_swapped:
                target = 1 if f1_won else 0
                name_pos1, name_pos2 = f1, f2
                odds_pos1, odds_pos2 = odds_f1_val, odds_f2_val

                delta_elo = delta_elo_raw
                delta_win_streak = delta_win_streak_raw
                delta_loss_streak = delta_loss_streak_raw
                delta_win_rate_last_5 = delta_win_rate_last_5_raw
                delta_ufc_win_rate = delta_ufc_win_rate_raw
                delta_ufc_fights = delta_ufc_fights_raw
                delta_rank = delta_rank_raw
                is_ranked_p1 = is_ranked_f1_raw
                is_ranked_p2 = is_ranked_f2_raw

                delta_win_rate_3y = delta_win_rate_3y_raw
                delta_SlpM_3y = delta_SlpM_3y_raw
                delta_SApM_3y = delta_SApM_3y_raw
                delta_TD_Def_3y = delta_TD_Def_3y_raw

                deltas_v1 = deltas_v1_raw
            else:
                target = 1 if not f1_won else 0
                name_pos1, name_pos2 = f2, f1
                odds_pos1, odds_pos2 = odds_f2_val, odds_f1_val

                delta_elo = -delta_elo_raw
                delta_win_streak = -delta_win_streak_raw
                delta_loss_streak = -delta_loss_streak_raw
                delta_win_rate_last_5 = -delta_win_rate_last_5_raw
                delta_ufc_win_rate = -delta_ufc_win_rate_raw
                delta_ufc_fights = -delta_ufc_fights_raw
                delta_rank = -delta_rank_raw
                is_ranked_p1 = is_ranked_f2_raw
                is_ranked_p2 = is_ranked_f1_raw

                delta_win_rate_3y = -delta_win_rate_3y_raw if pd.notna(delta_win_rate_3y_raw) else np.nan
                delta_SlpM_3y = -delta_SlpM_3y_raw if pd.notna(delta_SlpM_3y_raw) else np.nan
                delta_SApM_3y = -delta_SApM_3y_raw if pd.notna(delta_SApM_3y_raw) else np.nan
                delta_TD_Def_3y = -delta_TD_Def_3y_raw if pd.notna(delta_TD_Def_3y_raw) else np.nan

                deltas_v1 = {k: -v if pd.notna(v) else np.nan for k, v in deltas_v1_raw.items()}

            event_dt_str = event_dt.strftime("%Y-%m-%d")

            row_dict = {
                "f_1_name": name_pos1,
                "f_2_name": name_pos2,
                "f_1_odds": odds_pos1,
                "f_2_odds": odds_pos2,
                "event_date": event_dt_str,
                "Y": target,
                # Features V1
                **deltas_v1,
                # Features V2
                "delta_elo": delta_elo,
                "delta_win_streak": delta_win_streak,
                "delta_loss_streak": delta_loss_streak,
                "delta_win_rate_last_5": delta_win_rate_last_5,
                "delta_ufc_win_rate": delta_ufc_win_rate,
                "delta_ufc_fights": delta_ufc_fights,
                "delta_rank": delta_rank,
                "is_ranked_f1": is_ranked_p1,
                "is_ranked_f2": is_ranked_p2,
                # Features V3 (3-year rolling)
                "delta_win_rate_3y": delta_win_rate_3y,
                "delta_SlpM_3y": delta_SlpM_3y,
                "delta_SApM_3y": delta_SApM_3y,
                "delta_TD_Def_3y": delta_TD_Def_3y
            }
            processed_rows.append(row_dict)

    processed_df = pd.DataFrame(processed_rows)

    # 4. Imputation par la médiane
    print(f"\n4. Imputation des nans par la médiane sur le sous-ensemble filtré (2010-2026 : {len(processed_df)} combats)...")
    feature_cols = [c for c in processed_df.columns if c.startswith("delta_") or c.startswith("is_ranked_")]
    medians_dict = {}

    for col in feature_cols:
        median_val = float(processed_df[col].median(skipna=True))
        if pd.isna(median_val):
            median_val = 0.0
        medians_dict[col] = median_val
        missing_count = processed_df[col].isna().sum()
        if missing_count > 0:
            processed_df[col] = processed_df[col].fillna(median_val)
            print(f"   -> {col} : {missing_count} nans imputés avec la médiane ({median_val:.4f})")

    # Enregistrement des médianes V3
    os.makedirs(os.path.dirname(MEDIANS_V3_PATH), exist_ok=True)
    with open(MEDIANS_V3_PATH, "w", encoding="utf-8") as f:
        json.dump(medians_dict, f, indent=4)
    print(f"   -> Médianes V3 sauvegardées dans : {MEDIANS_V3_PATH}")

    # Exportation du dataset V3 avec cotes
    os.makedirs(os.path.dirname(PROCESSED_DATA_V3_PATH), exist_ok=True)
    processed_df.to_csv(PROCESSED_DATA_V3_PATH, index=False)
    print(f"\n5. Dataset Features V3 (avec cotes) sauvegardé dans : {PROCESSED_DATA_V3_PATH}")

    print("\n" + "=" * 65)
    print("RÉSUMÉ STATISTIQUE DU DATASET V3 (avec cotes de marché) :")
    print(f"Total de combats conservés : {len(processed_df)}")
    print(f"Nombre de cotes renseignées : f_1_odds={processed_df['f_1_odds'].notna().sum()}, f_2_odds={processed_df['f_2_odds'].notna().sum()}")
    print("=" * 65)

    return processed_df


if __name__ == "__main__":
    load_and_preprocess_v3()
