"""
Script dédié de calibration des probabilités pour le modèle UFC V3 Optimal.
Évalue 3 versions sur le jeu de test (2015-2026, lambda=0.070) :
1. Modèle Brut XGBoost (Non calibré)
2. Calibration Sigmoïde (Platt Scaling)
3. Calibration Isotonique (Isotonic Regression)

Calcule : Brier Score, LogLoss, ECE (Expected Calibration Error), Accuracy Globale et Accuracy Confiance >=65%.
Sauvegarde le modèle calibré sous models/ufc_xgboost_model_v3_calibrated.pkl.
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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, brier_score_loss

PROCESSED_DATA_V3_PATH = os.path.join("data", "processed", "ufc_features_delta_v3.csv")
MODEL_CALIBRATED_OUTPUT_PATH = os.path.join("models", "ufc_xgboost_model_v3_calibrated.pkl")
METADATA_CALIBRATED_OUTPUT_PATH = os.path.join("models", "model_metadata_v3_calibrated.json")


def compute_ece(y_true, y_prob, n_bins=10):
    """Calcule l'Expected Calibration Error (ECE)."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    total_samples = len(y_true)
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin
    return float(ece)


def run_calibration():
    print("=" * 95)
    print(" 🎯 CALIBRATION DES PROBABILITÉS DU MODÈLE UFC V3 OPTIMAL (2015-2026, LAMBDA=0.070) 🎯")
    print("=" * 95)

    if not os.path.exists(PROCESSED_DATA_V3_PATH):
        raise FileNotFoundError(f"Le fichier {PROCESSED_DATA_V3_PATH} est introuvable. Exécutez d'abord src/data_prep.py.")

    df_full = pd.read_csv(PROCESSED_DATA_V3_PATH)
    df_full["event_date"] = pd.to_datetime(df_full["event_date"], errors="coerce")

    # Filtrage 2015-2026
    df = df_full[df_full["event_date"] >= "2015-01-01"].copy().reset_index(drop=True)
    print(f"   -> Dataset Ère Moderne (2015-2026) chargé : {len(df)} combats")

    feature_cols = [col for col in df.columns if col.startswith("delta_") or col.startswith("is_ranked_")]
    X = df[feature_cols]
    y = df["Y"]
    dates = df["event_date"]

    t_max = dates.max()

    # Split Train (80%) / Test (20%) avec seed=42
    X_train, X_test, y_train, y_test, dates_train, dates_test = train_test_split(
        X, y, dates, test_size=0.20, random_state=42, stratify=y
    )

    days_elapsed_train = (t_max - dates_train).dt.days
    lambda_optimal = 0.070
    sw_train = np.exp(-lambda_optimal * (days_elapsed_train / 365.25))

    print(f"   -> Sample weights calculés avec lambda = {lambda_optimal} (min={sw_train.min():.4f}, max={sw_train.max():.4f})")

    # 1. Modèle de base XGBoost brut (Non calibré)
    print("\n   [1] Entraînement du modèle de base XGBoost brut...")
    base_model = XGBClassifier(
        n_estimators=150,
        learning_rate=0.03,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss"
    )
    base_model.fit(X_train, y_train, sample_weight=sw_train)

    # 2. Modèle Calibré Sigmoïde (Platt Scaling)
    print("   [2] Entraînement de la calibration Sigmoïde (Platt Scaling)...")
    sig_model = CalibratedClassifierCV(
        estimator=XGBClassifier(
            n_estimators=150, learning_rate=0.03, max_depth=4,
            subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric="logloss"
        ),
        method="sigmoid",
        cv=5
    )
    sig_model.fit(X_train, y_train, sample_weight=sw_train)

    # 3. Modèle Calibré Isotonique (Isotonic Regression)
    print("   [3] Entraînement de la calibration Isotonique...")
    iso_model = CalibratedClassifierCV(
        estimator=XGBClassifier(
            n_estimators=150, learning_rate=0.03, max_depth=4,
            subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric="logloss"
        ),
        method="isotonic",
        cv=5
    )
    iso_model.fit(X_train, y_train, sample_weight=sw_train)

    models_dict = {
        "Modèle Brut (Non calibré)": base_model,
        "Calibré Sigmoïde (Platt Scaling)": sig_model,
        "Calibré Isotonique": iso_model
    }

    results = []
    best_calibrated_model = None
    best_calibrated_name = ""
    best_brier = 999.0

    for name, mdl in models_dict.items():
        y_prob = mdl.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        max_prob = np.maximum(y_prob, 1.0 - y_prob)

        brier = brier_score_loss(y_test, y_prob)
        loss = log_loss(y_test, y_prob)
        ece = compute_ece(y_test.values, y_prob)
        acc_g = accuracy_score(y_test, y_pred)

        c60 = max_prob >= 0.60
        acc_60 = accuracy_score(y_test[c60], y_pred[c60]) if c60.sum() > 0 else acc_g

        c65 = max_prob >= 0.65
        acc_65 = accuracy_score(y_test[c65], y_pred[c65]) if c65.sum() > 0 else acc_g

        if brier < best_brier:
            best_brier = brier
            best_calibrated_model = mdl
            best_calibrated_name = name

        results.append({
            "name": name,
            "brier": brier,
            "logloss": loss,
            "ece": ece,
            "acc_global": acc_g,
            "acc_c60": acc_60,
            "acc_c65": acc_65
        })

    # Tableau récapitulatif
    print("\n" + "=" * 105)
    print(" 📊 TABLEAU COMPARATIF DES MÉTHODES DE CALIBRATION 📊")
    print("=" * 105)
    header = f"| {'Méthode de Calibration':<35} | {'Brier Score':<11} | {'LogLoss':<8} | {'ECE (Erreur)':<12} | {'Acc. Globale':<12} | {'Acc. Conf >=65%':<16} |"
    print(header)
    print("|" + "-" * 37 + "|" + "-" * 13 + "|" + "-" * 10 + "|" + "-" * 14 + "|" + "-" * 14 + "|" + "-" * 18 + "|")

    for r in results:
        star = "  <-- BEST" if r["name"] == best_calibrated_name else ""
        row_str = f"| {r['name']:<35} | {r['brier']:<11.5f} | {r['logloss']:<8.4f} | {r['ece']*100:<11.2f}% | {r['acc_global']*100:<11.2f}% | {r['acc_c65']*100:<15.2f}% |{star}"
        print(row_str)

    print("=" * 105)
    print(f"\n 🏆 MEILLEURE MÉTHODE DE CALIBRATION : {best_calibrated_name}")

    # Sauvegarde du modèle calibré optimal
    os.makedirs(os.path.dirname(MODEL_CALIBRATED_OUTPUT_PATH), exist_ok=True)
    joblib.dump(best_calibrated_model, MODEL_CALIBRATED_OUTPUT_PATH)
    print(f"   -> Modèle calibré sauvegardé dans : {MODEL_CALIBRATED_OUTPUT_PATH}")

    best_res = next(r for r in results if r["name"] == best_calibrated_name)
    metadata = {
        "calibration_method": best_calibrated_name,
        "lambda": lambda_optimal,
        "brier_score": float(best_res["brier"]),
        "logloss": float(best_res["logloss"]),
        "ece": float(best_res["ece"]),
        "accuracy_global": float(best_res["acc_global"]),
        "accuracy_conf_65": float(best_res["acc_c65"]),
        "feature_cols": feature_cols
    }
    with open(METADATA_CALIBRATED_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"   -> Métadonnées de calibration sauvegardées dans : {METADATA_CALIBRATED_OUTPUT_PATH}")

    print("=" * 95 + "\n")


if __name__ == "__main__":
    run_calibration()
