"""
Script de recherche sur grille 2D (Start Year x Lambda Time Decay).
Évalue 9 combinaisons (start_years=[2010, 2015, 2018] x lambdas=[0.00, 0.02, 0.05])
sur un jeu de test commun et figé (20% des combats post-2021).
Sauvegarde le meilleur modèle dans models/ufc_xgboost_model_v3.pkl.
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

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

PROCESSED_DATA_V3_PATH = os.path.join("data", "processed", "ufc_features_delta_v3.csv")
MODEL_V3_OUTPUT_PATH = os.path.join("models", "ufc_xgboost_model_v3.pkl")
METADATA_V3_OUTPUT_PATH = os.path.join("models", "model_metadata_v3.json")


def run_grid_search_2d():
    print("=" * 85)
    print(" RECHERCHE SUR GRILLE 2D (START YEAR x TIME DECAY LAMBDA)")
    print("=" * 85)

    if not os.path.exists(PROCESSED_DATA_V3_PATH):
        raise FileNotFoundError(f"Le fichier {PROCESSED_DATA_V3_PATH} est introuvable. Exécutez d'abord src/data_prep.py.")

    df = pd.read_csv(PROCESSED_DATA_V3_PATH)
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    print(f"   -> Dataset complet chargé : {len(df)} combats (2010–2026)")

    feature_cols = [col for col in df.columns if col.startswith("delta_") or col.startswith("is_ranked_")]

    # 1. Isolation d'un JEU DE TEST COMMUN ET FIGÉ (20% des combats >= 2021-01-01)
    df_recent = df[df["event_date"] >= "2021-01-01"].copy()
    df_pre_2021 = df[df["event_date"] < "2021-01-01"].copy()

    # Train / Test split 80/20 sur les combats récents
    recent_train_idx, recent_test_idx = train_test_split(
        df_recent.index, test_size=0.20, random_state=42, stratify=df_recent["Y"]
    )

    test_df = df_recent.loc[recent_test_idx].copy()
    candidate_train_df = pd.concat([df_pre_2021, df_recent.loc[recent_train_idx]]).sort_values(by="event_date").reset_index(drop=True)

    print(f"   -> Test Set commun figé (post-2021) : {len(test_df)} combats")
    print(f"   -> Pool de candidats pour l'entraînement : {len(candidate_train_df)} combats")

    X_test_common = test_df[feature_cols]
    y_test_common = test_df["Y"]
    dates_test_common = test_df["event_date"]

    t_max = df["event_date"].max()

    # 2. Grille 2D
    start_years = [2010, 2015, 2018]
    lambdas = [0.00, 0.02, 0.05]

    results = []
    best_model = None
    best_combo = None
    best_score = -1.0

    print("\n   [+] Exécution des 9 expérimentations 2D...\n")

    for sy in start_years:
        cutoff_date = pd.Timestamp(f"{sy}-01-01")
        sub_train_df = candidate_train_df[candidate_train_df["event_date"] >= cutoff_date].copy()

        X_tr = sub_train_df[feature_cols]
        y_tr = sub_train_df["Y"]
        dates_tr = sub_train_df["event_date"]

        days_elapsed_tr = (t_max - dates_tr).dt.days

        for lmb in lambdas:
            if lmb == 0.00:
                sw_tr = None
            else:
                sw_tr = np.exp(-lmb * (days_elapsed_tr / 365.25))

            model = XGBClassifier(
                n_estimators=150,
                learning_rate=0.03,
                max_depth=4,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric="logloss"
            )

            model.fit(X_tr, y_tr, sample_weight=sw_tr)

            # Évaluation sur le Test Set commun
            y_pred_global = model.predict(X_test_common)
            y_prob_global = model.predict_proba(X_test_common)[:, 1]

            acc_global = accuracy_score(y_test_common, y_pred_global)
            roc_auc_global = roc_auc_score(y_test_common, y_prob_global)

            # Test set 5 ans (post-2021)
            mask_5y = dates_test_common >= "2021-01-01"
            acc_5y = accuracy_score(y_test_common[mask_5y], y_pred_global[mask_5y]) if mask_5y.sum() > 0 else 0.0

            # Test set 1 an (post-2025)
            mask_1y = dates_test_common >= "2025-01-01"
            acc_1y = accuracy_score(y_test_common[mask_1y], y_pred_global[mask_1y]) if mask_1y.sum() > 0 else 0.0

            # Combined score prioritising 1-year and 5-year accuracy
            combined_score = 0.50 * acc_1y + 0.30 * acc_5y + 0.20 * acc_global

            if combined_score > best_score:
                best_score = combined_score
                best_model = model
                best_combo = (sy, lmb)

            results.append({
                "start_year": sy,
                "lambda": lmb,
                "train_size": len(sub_train_df),
                "acc_global": acc_global,
                "acc_5y": acc_5y,
                "acc_1y": acc_1y,
                "roc_auc": roc_auc_global,
                "combined_score": combined_score
            })

    # Tri des résultats par Accuracy 1 an décroissante (puis Acc 5 ans)
    results_sorted = sorted(results, key=lambda r: (r["acc_1y"], r["acc_5y"], r["acc_global"]), reverse=True)

    # Affichage du tableau récapitulatif
    print("=" * 95)
    print(" TABLEAU COMPARATIF DES 9 EXPÉRIMENTATIONS 2D (Trie par Acc. 1 An)")
    print("=" * 95)
    header = f"| {'Start Year':<10} | {'Lambda':<6} | {'Train Size':<10} | {'Acc. Globale':<12} | {'Acc. 5 ans (2021-26)':<19} | {'Acc. 1 an (2025-26)':<18} | {'ROC-AUC':<7} |"
    print(header)
    print("|" + "-" * 12 + "|" + "-" * 8 + "|" + "-" * 12 + "|" + "-" * 14 + "|" + "-" * 21 + "|" + "-" * 20 + "|" + "-" * 9 + "|")

    for r in results_sorted:
        star = "  <-- BEST" if (r["start_year"] == best_combo[0] and r["lambda"] == best_combo[1]) else ""
        row_str = f"| {r['start_year']:<10} | {r['lambda']:<6.2f} | {r['train_size']:<10} | {r['acc_global']*100:<11.2f}% | {r['acc_5y']*100:<18.2f}% | {r['acc_1y']*100:<17.2f}% | {r['roc_auc']:<7.4f} |{star}"
        print(row_str)

    print("=" * 95)
    print(f"\n [MEILLEURE COMBINAISON DETECTEE] : Start Year = {best_combo[0]}, Lambda = {best_combo[1]:.2f}")

    # Sauvegarde du meilleur modèle
    os.makedirs(os.path.dirname(MODEL_V3_OUTPUT_PATH), exist_ok=True)
    joblib.dump(best_model, MODEL_V3_OUTPUT_PATH)
    print(f"   -> Meilleur modèle sauvegardé dans : {MODEL_V3_OUTPUT_PATH}")

    fi_df = pd.DataFrame({
        "Feature": feature_cols,
        "Importance": best_model.feature_importances_
    }).sort_values(by="Importance", ascending=False)

    fi_dict = {str(row['Feature']): float(row['Importance']) for _, row in fi_df.iterrows()}

    best_res = next(r for r in results if r["start_year"] == best_combo[0] and r["lambda"] == best_combo[1])
    metadata_v3 = {
        "best_start_year": int(best_combo[0]),
        "best_lambda": float(best_combo[1]),
        "train_size": int(best_res["train_size"]),
        "accuracy_global": float(best_res["acc_global"]),
        "accuracy_5y": float(best_res["acc_5y"]),
        "accuracy_1y": float(best_res["acc_1y"]),
        "roc_auc": float(best_res["roc_auc"]),
        "feature_cols": feature_cols,
        "n_estimators": 150,
        "learning_rate": 0.03,
        "max_depth": 4,
        "feature_importances": fi_dict
    }
    with open(METADATA_V3_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata_v3, f, indent=4)
    print(f"   -> Métadonnées mises à jour dans : {METADATA_V3_OUTPUT_PATH}")

    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_grid_search_2d()
