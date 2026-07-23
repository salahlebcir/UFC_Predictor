"""
Script d'analyse approfondie à haute résolution (Deep Lambda Search v2) sur la période 2015-2026.
Évalue 13 valeurs de lambda sur 10 graines aléatoires (130 modèles entraînés)
avec mesure de l'accuracy multi-fenêtres, l'accuracy par seuil de confiance (>=55%, >=60%, >=65%),
le Brier Score, la LogLoss et le ROC-AUC.
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
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, brier_score_loss

PROCESSED_DATA_V3_PATH = os.path.join("data", "processed", "ufc_features_delta_v3.csv")
MODEL_V3_OUTPUT_PATH = os.path.join("models", "ufc_xgboost_model_v3.pkl")
METADATA_V3_OUTPUT_PATH = os.path.join("models", "model_metadata_v3.json")


def run_deep_lambda_search_v2():
    print("=" * 95)
    print(" 🔬 DEEP LAMBDA SEARCH V2 - ANALYSE ENRICHI HAUTE RÉSOLUTION (2015-2026) 🔬")
    print("=" * 95)

    if not os.path.exists(PROCESSED_DATA_V3_PATH):
        raise FileNotFoundError(f"Le fichier {PROCESSED_DATA_V3_PATH} est introuvable. Exécutez d'abord src/data_prep.py.")

    df_full = pd.read_csv(PROCESSED_DATA_V3_PATH)
    df_full["event_date"] = pd.to_datetime(df_full["event_date"], errors="coerce")

    # 1. Filtrage sur la période 2015-2026
    df = df_full[df_full["event_date"] >= "2015-01-01"].copy().reset_index(drop=True)
    print(f"   -> Dataset filtré sur l'Ère Moderne 2015-2026 : {len(df)} combats")

    feature_cols = [col for col in df.columns if col.startswith("delta_") or col.startswith("is_ranked_")]
    X_full = df[feature_cols]
    y_full = df["Y"]
    dates_full = df["event_date"]

    t_max = dates_full.max()

    # 2. Grille de test à haute résolution
    lambdas = [0.000, 0.005, 0.010, 0.015, 0.020, 0.025, 0.030, 0.040, 0.050, 0.070, 0.100, 0.125, 0.150]
    seeds = [42, 100, 2024, 777, 999, 123, 456, 888, 2025, 2026]

    print(f"   -> Grille : {len(lambdas)} lambdas x {len(seeds)} tirages = {len(lambdas) * len(seeds)} modèles à entraîner")
    print("\n   [+] Exécution des simulations...\n")

    summary_results = []
    best_overall_model = None
    best_overall_score = 999.0  # Min brier score / logloss
    best_overall_lambda = None

    for lmb in lambdas:
        acc_global_list = []
        acc_5y_list = []
        acc_3y_list = []
        acc_1y_list = []

        acc_conf_55_list = []
        acc_conf_60_list = []
        acc_conf_65_list = []

        brier_list = []
        logloss_list = []
        roc_auc_list = []

        last_fitted_model = None

        for seed in seeds:
            X_tr, X_te, y_tr, y_te, dates_tr, dates_te = train_test_split(
                X_full, y_full, dates_full, test_size=0.20, random_state=seed, stratify=y_full
            )

            days_elapsed_tr = (t_max - dates_tr).dt.days

            if lmb == 0.000:
                sw_tr = None
            else:
                sw_tr = np.exp(-lmb * (days_elapsed_tr / 365.25))

            model = XGBClassifier(
                n_estimators=150,
                learning_rate=0.03,
                max_depth=4,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=seed,
                eval_metric="logloss"
            )

            model.fit(X_tr, y_tr, sample_weight=sw_tr)
            last_fitted_model = model

            y_pred = model.predict(X_te)
            y_prob = model.predict_proba(X_te)[:, 1]

            # Probabilité max (confiance de la prédiction)
            max_prob = np.maximum(y_prob, 1.0 - y_prob)

            # Métriques
            acc_g = accuracy_score(y_te, y_pred)
            brier = brier_score_loss(y_te, y_prob)
            loss = log_loss(y_te, y_prob)
            auc = roc_auc_score(y_te, y_prob)

            acc_global_list.append(acc_g)
            brier_list.append(brier)
            logloss_list.append(loss)
            roc_auc_list.append(auc)

            # Accuracy par fenêtre temporelle
            m_5y = dates_te >= "2021-01-01"
            acc_5y_list.append(accuracy_score(y_te[m_5y], y_pred[m_5y]) if m_5y.sum() > 0 else acc_g)

            m_3y = dates_te >= "2023-01-01"
            acc_3y_list.append(accuracy_score(y_te[m_3y], y_pred[m_3y]) if m_3y.sum() > 0 else acc_g)

            m_1y = dates_te >= "2025-01-01"
            acc_1y_list.append(accuracy_score(y_te[m_1y], y_pred[m_1y]) if m_1y.sum() > 0 else acc_g)

            # Accuracy par seuil de confiance
            c55 = max_prob >= 0.55
            acc_conf_55_list.append(accuracy_score(y_te[c55], y_pred[c55]) if c55.sum() > 0 else acc_g)

            c60 = max_prob >= 0.60
            acc_conf_60_list.append(accuracy_score(y_te[c60], y_pred[c60]) if c60.sum() > 0 else acc_g)

            c65 = max_prob >= 0.65
            acc_conf_65_list.append(accuracy_score(y_te[c65], y_pred[c65]) if c65.sum() > 0 else acc_g)

        # Moyennes pour cette valeur de lambda
        mean_brier = float(np.mean(brier_list))
        mean_logloss = float(np.mean(logloss_list))

        if mean_brier < best_overall_score:
            best_overall_score = mean_brier
            best_overall_model = last_fitted_model
            best_overall_lambda = lmb

        summary_results.append({
            "lambda": lmb,
            "acc_global": float(np.mean(acc_global_list)),
            "acc_5y": float(np.mean(acc_5y_list)),
            "acc_3y": float(np.mean(acc_3y_list)),
            "acc_1y": float(np.mean(acc_1y_list)),
            "acc_c55": float(np.mean(acc_conf_55_list)),
            "acc_c60": float(np.mean(acc_conf_60_list)),
            "acc_c65": float(np.mean(acc_conf_65_list)),
            "brier": mean_brier,
            "logloss": mean_logloss,
            "roc_auc": float(np.mean(roc_auc_list))
        })

    # Tri par Brier Score croissant (meilleure calibration des probabilités)
    summary_sorted = sorted(summary_results, key=lambda x: x["brier"])

    print("=" * 115)
    print(" 📊 TABLEAU SYNTHÉTIQUE COMPLET (Moyenne sur 10 Seeds - Trie par Brier Score) 📊")
    print("=" * 115)
    header = f"| {'Lambda':<6} | {'Acc. Glob.':<10} | {'Acc. 1 An (2025-26)':<19} | {'Acc. Conf>=60%':<14} | {'Acc. Conf>=65%':<14} | {'Brier Score':<11} | {'LogLoss':<8} | {'ROC-AUC':<7} |"
    print(header)
    print("|" + "-" * 8 + "|" + "-" * 12 + "|" + "-" * 21 + "|" + "-" * 16 + "|" + "-" * 16 + "|" + "-" * 13 + "|" + "-" * 10 + "|" + "-" * 9 + "|")

    for r in summary_sorted:
        star = "  <-- BEST CALIBRATED" if r["lambda"] == best_overall_lambda else ""
        row_str = f"| {r['lambda']:<6.3f} | {r['acc_global']*100:<9.2f}% | {r['acc_1y']*100:<18.2f}% | {r['acc_c60']*100:<13.2f}% | {r['acc_c65']*100:<13.2f}% | {r['brier']:<11.5f} | {r['logloss']:<8.4f} | {r['roc_auc']:<7.4f} |{star}"
        print(row_str)

    print("=" * 115)

    # Re-détecter le lambda maximisant l'accuracy 1 an / 3 ans
    best_acc_1y_item = max(summary_results, key=lambda x: x["acc_1y"])
    best_acc_3y_item = max(summary_results, key=lambda x: x["acc_3y"])
    best_c65_item = max(summary_results, key=lambda x: x["acc_c65"])

    print("\n 💡 SYNTHÈSE ET ANALYSE EXPLICATIVE :")
    print(f"   • Lambda maximisant l'Accuracy 1 An (2025-2026) : lambda = {best_acc_1y_item['lambda']:.3f} ({best_acc_1y_item['acc_1y']*100:.2f}%)")
    print(f"   • Lambda maximisant l'Accuracy 3 Ans (2023-2026) : lambda = {best_acc_3y_item['lambda']:.3f} ({best_acc_3y_item['acc_3y']*100:.2f}%)")
    print(f"   • Lambda maximisant la Haute Confiance (>=65%)  : lambda = {best_c65_item['lambda']:.3f} ({best_c65_item['acc_c65']*100:.2f}%)")
    print(f"   • Lambda avec le Meilleur Brier Score & LogLoss  : lambda = {best_overall_lambda:.3f} (Brier: {best_overall_score:.5f})")

    # Sauvegarde du modèle optimal (modèle entraîné avec le meilleur lambda sur seed 42 pour la reproductibilité)
    best_lambda_to_save = best_overall_lambda
    X_tr_final, X_te_final, y_tr_final, y_te_final, dates_tr_final, dates_te_final = train_test_split(
        X_full, y_full, dates_full, test_size=0.20, random_state=42, stratify=y_full
    )
    days_elapsed_tr_final = (t_max - dates_tr_final).dt.days
    sw_tr_final = None if best_lambda_to_save == 0.0 else np.exp(-best_lambda_to_save * (days_elapsed_tr_final / 365.25))

    final_model = XGBClassifier(
        n_estimators=150,
        learning_rate=0.03,
        max_depth=4,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric="logloss"
    )
    final_model.fit(X_tr_final, y_tr_final, sample_weight=sw_tr_final)

    os.makedirs(os.path.dirname(MODEL_V3_OUTPUT_PATH), exist_ok=True)
    joblib.dump(final_model, MODEL_V3_OUTPUT_PATH)
    print(f"\n   [+] Modèle optimal (lambda = {best_lambda_to_save:.3f}) sauvegardé dans : {MODEL_V3_OUTPUT_PATH}")

    fi_df = pd.DataFrame({
        "Feature": feature_cols,
        "Importance": final_model.feature_importances_
    }).sort_values(by="Importance", ascending=False)
    fi_dict = {str(row['Feature']): float(row['Importance']) for _, row in fi_df.iterrows()}

    best_res_final = next(r for r in summary_results if r["lambda"] == best_lambda_to_save)
    metadata = {
        "best_lambda": float(best_lambda_to_save),
        "accuracy_global": float(best_res_final["acc_global"]),
        "accuracy_1y": float(best_res_final["acc_1y"]),
        "accuracy_3y": float(best_res_final["acc_3y"]),
        "accuracy_conf_65": float(best_res_final["acc_c65"]),
        "brier_score": float(best_res_final["brier"]),
        "logloss": float(best_res_final["logloss"]),
        "roc_auc": float(best_res_final["roc_auc"]),
        "feature_cols": feature_cols,
        "n_estimators": 150,
        "learning_rate": 0.03,
        "max_depth": 4,
        "feature_importances": fi_dict
    }
    with open(METADATA_V3_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"   [+] Métadonnées sauvegardées dans : {METADATA_V3_OUTPUT_PATH}")

    print("=" * 95 + "\n")


if __name__ == "__main__":
    run_deep_lambda_search_v2()
