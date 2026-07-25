"""
UFC Vision — Script de Chauffage de Cache (Background Warm-up & Cron Job)
Exécute en arrière-plan le rafraîchissement autonome de The Odds API,
la synchronisation de l'historique et le chauffage de l'application Streamlit.

Usage :
    python warmup.py            # Mode exécution unique (Idéal pour Cron Job toutes les 2h)
    python warmup.py --daemon   # Mode démon permanent (Boucle infinie toutes les 2h / 7200s)
    python warmup.py --port 8501 # Spécifier le port de l'application Streamlit
"""

import os
import sys
import time
import argparse
import urllib.request
from datetime import datetime

# Garantie d'inclusion du dossier racine et du dossier src dans sys.path
project_root = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(project_root, "src")
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Imports des modules du backend (SOC - Strictement intact)
try:
    from src.odds_api import get_cached_or_fresh_odds
    from src.predict import load_resources_v3
    from src.historical_tracker import sync_historical_tracker
except ImportError:
    from odds_api import get_cached_or_fresh_odds
    from predict import load_resources_v3
    from historical_tracker import sync_historical_tracker


def run_cache_warmup(port=8501, force_refresh=False):
    """
    Exécute le cycle complet de chauffage de cache :
    1. Contrôle du cache The Odds API (TTL 2h strict, max 360 requêtes/mois sur le quota de 500)
    2. Récupère le modèle XGBoost V3 et les données dynamiques
    3. Synchronise le tracker d'historique et sauvegarde data/historical_tracker.json
    4. Effectue une requête HTTP vers Streamlit (http://localhost:port) pour pré-charger les caches en mémoire
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 75)
    print(f" 🚀 UFC VISION — CHAUFFAGE DE CACHE EN ARRIÈRE-PLAN [{now_str}]")
    print("=" * 75)

    # 1. Chauffage des Cotes (TTL 2h strict)
    print("\n [1/4] 🔄 Contrôle et rafraîchissement des cotes (The Odds API)...")
    try:
        events, from_cache, age_hours = get_cached_or_fresh_odds(force_refresh=force_refresh)
        event_count = len(events) if events else 0
        if from_cache:
            print(f"   [✓] Cache local valide (Âge : {age_hours:.2f}h < 2h). 0 appel API consommé.")
        else:
            print(f"   [✓] Cotes actualisées via The Odds API (1 appel API effectué) : {event_count} événements enregistrés.")
    except Exception as e:
        print(f"   [!] Erreur lors du rafraîchissement des cotes : {e}")
        events = None

    # 2. Chargement des ressources V3
    print("\n [2/4] 🧠 Chargement du modèle XGBoost V3 et des structures de données...")
    try:
        model, raw_df, medians, all_fighters, _ = load_resources_v3()
        print("   [✓] Modèle et dataset V3 chargés.")
    except Exception as e:
        print(f"   [!] Erreur lors du chargement des ressources V3 : {e}")
        return False

    # 3. Synchronisation du Tracker Historique
    print("\n [3/4] 📊 Synchronisation autonome du tracker d'historique...")
    try:
        upcoming, past, summary = sync_historical_tracker(events, raw_df, model, medians, all_fighters)
        profit = summary.get("total_profit", 0.0)
        roi = summary.get("roi_pct", 0.0)
        print(f"   [✓] Tracker synchronisé : {len(upcoming)} cartes futures, {len(past)} cartes passées.")
        print(f"   [✓] Bilan Financier : Profit = {profit:+.2f} € | ROI = {roi:+.2f} %.")
    except Exception as e:
        print(f"   [!] Erreur lors de la synchronisation du tracker : {e}")

    # 4. Requête HTTP de Pré-Chauffage vers Streamlit
    print(f"\n [4/4] ⚡ Envoi de la requête de pré-chauffage à Streamlit (http://localhost:{port})...")
    streamlit_url = f"http://localhost:{port}"
    try:
        req = urllib.request.Request(
            streamlit_url,
            headers={"User-Agent": "UFCVision-WarmupBot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status == 200:
                print(f"   [✓] Streamlit pré-chauffé avec succès ! Code HTTP : {response.status}")
            else:
                print(f"   [!] Réponse Streamlit inattendue : Code {response.status}")
    except Exception as e:
        print(f"   [i] Streamlit non accessible sur http://localhost:{port} ({e}). (Le cache fichier est néanmoins prêt).")

    print("\n" + "=" * 75)
    print(f" ✨ FIN DU CHAUFFAGE DE CACHE [{datetime.now().strftime('%H:%M:%S')}] — Cache 100% Instantané")
    print("=" * 75 + "\n")
    return True


def main():
    parser = argparse.ArgumentParser(description="Chauffage de cache autonome pour UFC Vision (Limit strict 2h / Max 360 requêtes par mois)")
    parser.add_argument("--daemon", action="store_true", help="Exécuter en mode démon permanent (toutes les 2h / 7200s)")
    parser.add_argument("--force", action="store_true", help="Forcer le rafraîchissement des cotes même si le cache a moins de 2h")
    parser.add_argument("--interval", type=int, default=7200, help="Intervalle entre les rafraîchissements en secondes (Défaut: 7200s / 2h)")
    parser.add_argument("--port", type=int, default=8501, help="Port local du serveur Streamlit (Défaut: 8501)")
    args = parser.parse_args()

    if args.daemon:
        print(f"🟢 Mode Démon Actif — Exécution de warmup.py toutes les {args.interval // 3600} heures ({args.interval}s).")
        while True:
            try:
                run_cache_warmup(port=args.port, force_refresh=args.force)
            except Exception as err:
                print(f"[!] Erreur inattendue dans la boucle du démon : {err}")
            time.sleep(args.interval)
    else:
        run_cache_warmup(port=args.port, force_refresh=args.force)


if __name__ == "__main__":
    main()
