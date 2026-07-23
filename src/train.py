"""
Script d'entraînement et d'évaluation du modèle XGBoost V3 pour la prédiction des combats UFC.
Intègre la pondération temporelle (Time Decay lambda=0.15) et l'Ère Moderne (2010-2026).
Évaluation complète (Accuracy, ROC-AUC, Matrice de Confusion) et comparaison tri-modèle V1 vs V2 vs V3.
"""

import os
import json
import joblib
import pandas as pd
import numpy as np

from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix, classification_report

PROCESSED_DATA_V3_PATH = os.path.join("data", "processed", "ufc_features_delta_v3.csv")
MODEL_V3_OUTPUT_PATH = os.path.join("models", "ufc_xgboost_model_v3.pkl")
METADATA_V3_OUTPUT_PATH = os.path.join("models", "model_metadata_v3.json")

ACCURACY_V1 = 0.6477
ACCURACY_V2 = 0.6952
ROC_AUC_V2 = 0.7539


def train_model_v3():
    print("=" * 65)
    print("1. Chargement du dataset Features V3 (Ère Moderne 2010-2026)...")
    if not os.path.exists(PROCESSED_DATA_V3_PATH):
        raise FileNotFoundError(f"Le fichier {PROCESSED_DATA_V3_PATH} est introuvable. Exécutez d'abord src/data_prep.py.")

    df = pd.read_csv(PROCESSED_DATA_V3_PATH)
    print(f"   -> {len(df)} exemples chargés.")

    df["event_date"] = pd.to_datetime(df["event_date"], errors="coerce")

    # 2. Séparation X et Y
    feature_cols = [col for col in df.columns if col.startswith("delta_") or col.startswith("is_ranked_")]
    X = df[feature_cols]
    y = df["Y"]

    print(f"   -> Nombre total de caractéristiques (X) : {len(feature_cols)}")

    # 3. Calcul de la dépréciation temporelle (Time Decay Sample Weights)
    # T_max = date la plus récente
    t_max = df["event_date"].max()
    days_elapsed = (t_max - df["event_date"]).dt.days
    sample_weights = np.exp(-0.15 * (days_elapsed / 365.25))

    print(f"   -> Plage des poids d'échantillons Time Decay : min={sample_weights.min():.4f}, max={sample_weights.max():.4f}")

    # 4. Séparation Train (80%) et Test (20%)
    print("\n2. Division des données en Train (80%) et Test (20%)...")
    X_train, X_test, y_train, y_test, sw_train, sw_test = train_test_split(
        X, y, sample_weights, test_size=0.20, random_state=42, stratify=y
    )
    print(f"   -> Train set : {len(X_train)} exemples")
    print(f"   -> Test set  : {len(X_test)} exemples")

    # 5. Initialisation et entraînement de XGBoost V3 avec sample_weight
    print("\n3. Entraînement de XGBoost V3 avec pondération temporelle (sample_weight)...")
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
    print("   -> Entraînement V3 terminé avec succès.")

    # 6. Évaluation sur le Test Set (20%)
    print("\n4. Évaluation globale du modèle V3 sur le jeu de test...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc_v3 = accuracy_score(y_test, y_pred)
    roc_auc_v3 = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, target_names=["Défaite (0)", "Victoire (1)"])

    print("\n" + "=" * 65)
    print("   *** TABLEAU COMPARATIF TRI-MODÈLE UFC ***")
    print("=" * 65)
    print(f"   • V1 (1994-2026, 11 Features)          : {ACCURACY_V1 * 100:.2f}%")
    print(f"   • V2 (1994-2026, 20 Features)          : {ACCURACY_V2 * 100:.2f}% (ROC-AUC: {ROC_AUC_V2:.4f})")
    print(f"   • V3 (2010-2026, 24 Features + Decay) : {acc_v3 * 100:.2f}% (ROC-AUC: {roc_auc_v3:.4f})")
    print("=" * 65)

    print("\nMatrice de confusion V3 :")
    print(cm)
    print("\nRapport de classification détaillé V3 :")
    print(report)

    # 7. Importance des caractéristiques V3
    print("=" * 65)
    print("5. Classement d'importance des caractéristiques V3 :")
    importances = model.feature_importances_
    fi_df = pd.DataFrame({
        "Feature": feature_cols,
        "Importance": importances
    }).sort_values(by="Importance", ascending=False)

    fi_dict = {}
    for _, row in fi_df.iterrows():
        feat_name = str(row['Feature'])
        feat_imp = float(row['Importance'])
        fi_dict[feat_name] = feat_imp
        print(f"   - {feat_name:<24} : {feat_imp * 100:.2f}%")

    # 8. Sauvegarde du modèle V3 et des métadonnées
    os.makedirs(os.path.dirname(MODEL_V3_OUTPUT_PATH), exist_ok=True)
    joblib.dump(model, MODEL_V3_OUTPUT_PATH)
    print(f"\n6. Modèle V3 sauvegardé avec succès dans : {MODEL_V3_OUTPUT_PATH}")

    metadata_v3 = {
        "accuracy_v3": float(acc_v3),
        "accuracy_v2": float(ACCURACY_V2),
        "accuracy_v1": float(ACCURACY_V1),
        "roc_auc_v3": float(roc_auc_v3),
        "feature_cols": feature_cols,
        "n_estimators": 150,
        "learning_rate": 0.03,
        "max_depth": 4,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "lambda_time_decay": 0.15,
        "feature_importances": fi_dict
    }
    with open(METADATA_V3_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata_v3, f, indent=4)
    print(f"   -> Métadonnées V3 sauvegardées dans : {METADATA_V3_OUTPUT_PATH}")

    print("=" * 65)
    return model, acc_v3, fi_df


if __name__ == "__main__":
    train_model_v3()
