"""
Script de lancement unique pour l'application UFC Fight Predictor V3.
Vérifie l'existence des fichiers essentiels (dataset préparé, modèle XGBoost V3 calibré)
et lance automatiquement le Dashboard Web Streamlit (app.py).

Usage :
    python run.py
"""

import os
import sys
import subprocess

# Fix encoding stdout for Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROCESSED_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "ufc_features_delta_v3.csv")
MODEL_CALIBRATED_PATH = os.path.join(PROJECT_ROOT, "models", "ufc_xgboost_model_v3_calibrated.pkl")
MODEL_V3_PATH = os.path.join(PROJECT_ROOT, "models", "ufc_xgboost_model_v3.pkl")
APP_PATH = os.path.join(PROJECT_ROOT, "app.py")


def check_and_prepare_resources():
    """Vérifie la présence du dataset préparé V3 et du modèle XGBoost V3."""
    print("=" * 70)
    print(" 🥊 VÉRIFICATION DES RESSOURCES DE L'APPLICATION UFC PREDICATOR V3")
    print("=" * 70)

    # 1. Vérification du dataset préparé V3
    if not os.path.exists(PROCESSED_DATA_PATH):
        print("\n[!] Dataset V3 absent dans data/processed/ufc_features_delta_v3.csv.")
        print("   [+] Génération automatique du dataset V3 via src/data_prep.py...")
        data_prep_script = os.path.join(PROJECT_ROOT, "src", "data_prep.py")
        result = subprocess.run([sys.executable, data_prep_script], check=False)
        if result.returncode != 0:
            print("\n[ERROR] Échec de la préparation du dataset. Veuillez vérifier src/data_prep.py.")
            sys.exit(1)

    print("   [✓] Dataset préparé V3 prêt : data/processed/ufc_features_delta_v3.csv")

    # 2. Vérification du modèle V3 (calibré ou standard)
    if os.path.exists(MODEL_CALIBRATED_PATH):
        print(f"   [✓] Modèle calibré V3 prêt : {MODEL_CALIBRATED_PATH}")
    elif os.path.exists(MODEL_V3_PATH):
        print(f"   [✓] Modèle V3 prêt : {MODEL_V3_PATH}")
    else:
        print("\n[ERROR] Aucun modèle V3 trouvé dans models/. Entraînez le modèle via src/train.py ou src/calibrate_model.py.")
        sys.exit(1)

    print("-" * 70)


def warmup_cache():
    """Exécute le chauffage initial du cache avant le lancement de Streamlit."""
    print("\n   [🔥] Exécution du chauffage de cache initial (Odds API & Tracker)...")
    warmup_script = os.path.join(PROJECT_ROOT, "warmup.py")
    if os.path.exists(warmup_script):
        try:
            subprocess.run([sys.executable, warmup_script], check=False)
        except Exception as e:
            print(f"   [!] Avertissement lors du chauffage de cache : {e}")


def launch_streamlit_app():
    """Lance le Dashboard Streamlit (app.py)."""
    print("\n   [🚀] Lancement du Dashboard Web Streamlit (http://localhost:8501)...")
    print("=" * 70 + "\n")

    cmd = [sys.executable, "-m", "streamlit", "run", APP_PATH]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n\n[!] Application fermée par l'utilisateur.")
    except Exception as e:
        print(f"\n[ERROR] Impossible de lancer Streamlit : {e}")


def main():
    check_and_prepare_resources()
    warmup_cache()
    launch_streamlit_app()


if __name__ == "__main__":
    main()
