"""
Script de recherche sur grille (Grid Search) du paramètre de dépréciation temporelle (Time Decay lambda).
Évalue l'impact de lambda [0.00, 0.02, 0.05, 0.10, 0.15, 0.25] sur :
- l'Accuracy Globale (2010-2026)
- l'Accuracy sur 5 ans (2021-2026)
- l'Accuracy sur 1 an (2025-2026)
- le Score ROC-AUC Global
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


def run_grid_search_decay():
    print("=" * 85)
    print(" RECHERCHE SUR GRILLE DE LA DEPRECIATION TEMPORELLE (TIME DECAY LAMBDA)")
    print("=" * 85)

    if not os.path.exists(PROCESSED_DATA_V3_PATH):
        raise FileNotFoundError(f"Le fichier {PROCESSED_DATA_V3_PATH} est introuvable. Exécutez d'abord src/data_prep.py.")

    df = pd.read_csv(PROCESSED_DATA_V3_PATH)
    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")
    print(f"   -> Dataset charge : {len(df)} combats (2010-2026)")

    feature_cols = [col for col in df.columns if col.startswith("delta_") or col.startswith("is_ranked_")]
    X = df[feature_cols]
    y = df["Y"]
    dates = df["event_date"]

    X_train, X_test, y_train, y_test, dates_train, dates_test = train_test_split(
        X, y, dates, test_size=0.20, random_state=42, stratify=y
    )

    t_max = df["event_date"].max()
    days_elapsed_train = (t_max - dates_train).dt.days

    lambdas = [0.00, 0.02, 0.05, 0.10, 0.15, 0.25]
    results = []

    best_model = None
    best_lambda = None
    best_score = -1.0

    print("\n   [+] Execution des tests pour chaque valeur de lambda...\n")

    for lmb in lambdas:
        rel_weight_5y = float(np.exp(-lmb * 5.0))

        if lmb == 0.00:
            sw_train = None
        else:
            sw_train = np.exp(-lmb * (days_elapsed_train / 365.25))

        model = XGBClassifier(
            n_estimators=150,
            learning_rate=0.03,
            max_depth=4,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric="logloss"
        )

        model.fit(X_train, y_train, sample_weight=sw_train)

        y_pred_global = model.predict(X_test)
        y_prob_global = model.predict_proba(X_test)[:, 1]

        acc_global = accuracy_score(y_test, y_pred_global)
        roc_auc_global = roc_auc_score(y_test, y_prob_global)

        mask_5y = dates_test >= "2021-01-01"
        acc_5y = accuracy_score(y_test[mask_5y], y_pred_global[mask_5y]) if mask_5y.sum() > 0 else 0.0

        mask_1y = dates_test >= "2025-01-01"
        acc_1y = accuracy_score(y_test[mask_1y], y_pred_global[mask_1y]) if mask_1y.sum() > 0 else 0.0

        # Score combiné : priorité à l'accuracy recente (1 an et 5 ans) et la stabilité globale
        combined_score = 0.40 * acc_1y + 0.40 * acc_5y + 0.20 * acc_global

        if combined_score > best_score:
            best_score = combined_score
            best_model = model
            best_lambda = lmb

        results.append({
            "lambda": lmb,
            "weight_5y": rel_weight_5y,
            "acc_global": acc_global,
            "acc_5y": acc_5y,
            "acc_1y": acc_1y,
            "roc_auc": roc_auc_global,
            "combined_score": combined_score
        })

    print("=" * 95)
    print(" TABLEAU RECAPITULATIF COMPARATIF DES LAMBDAS (TIME DECAY)")
    print("=" * 95)
    header = f"| {'Lambda':<6} | {'Poids (5 ans)':<13} | {'Acc. Globale':<12} | {'Acc. 5 ans (2021-26)':<19} | {'Acc. 1 an (2025-26)':<18} | {'ROC-AUC':<7} |"
    print(header)
    print("|" + "-" * 8 + "|" + "-" * 15 + "|" + "-" * 14 + "|" + "-" * 21 + "|" + "-" * 20 + "|" + "-" * 9 + "|")

    for r in results:
        star = "  <-- BEST" if r["lambda"] == best_lambda else ""
        row_str = f"| {r['lambda']:<6.2f} | {r['weight_5y']:<13.2f} | {r['acc_global']*100:<11.2f}% | {r['acc_5y']*100:<18.2f}% | {r['acc_1y']*100:<17.2f}% | {r['roc_auc']:<7.4f} |{star}"
        print(row_str)

    print("=" * 95)
    print(f"\n [MEILLEUR LAMBDA DETECTE] : lambda = {best_lambda:.2f}")

    os.makedirs(os.path.dirname(MODEL_V3_OUTPUT_PATH), exist_ok=True)
    joblib.dump(best_model, MODEL_V3_OUTPUT_PATH)
    print(f"   -> Meilleur modele sauvegarde dans : {MODEL_V3_OUTPUT_PATH}")

    fi_df = pd.DataFrame({
        "Feature": feature_cols,
        "Importance": best_model.feature_importances_
    }).sort_values(by="Importance", ascending=False)

    fi_dict = {str(row['Feature']): float(row['Importance']) for _, row in fi_df.iterrows()}

    best_res = next(r for r in results if r["lambda"] == best_lambda)
    metadata_v3 = {
        "best_lambda": float(best_lambda),
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
    print(f"   -> Metadonnees mises a jour dans : {METADATA_V3_OUTPUT_PATH}")

    print("=" * 85 + "\n")


if __name__ == "__main__":
    run_grid_search_decay()
