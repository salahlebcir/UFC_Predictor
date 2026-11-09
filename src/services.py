"""
UFC Vision — Couche de Service Backend Unifiée (Backend Service Layer)
Sépare rigoureusement la logique métier et l'inférence ML de la couche de présentation (Frontend).
Expose des fonctions prêtes à l'emploi pour n'importe quel frontend (Streamlit, API REST FastAPI, Next.js, etc.).

Règles architecturales strictes :
1. ZÉRO appel réseau sortant lors des requêtes utilisateur (Lecture passive d'un cache local pré-calculé).
2. ZÉRO calcul lourd de Machine Learning ou manipulation de DataFrame dans la boucle de rendu du frontend.
3. Rigueur Point-in-Time absolue pour les cartes passées.
4. Compatibilité Unicode et chemins multi-plateformes (UTF-8 strict).
"""

import os
import sys
import json
import collections
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

# Forcer l'encodage UTF-8 sous Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# Définition des chemins absolus multi-plateformes
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
TRACKER_PATH = DATA_DIR / "historical_tracker.json"
ODDS_CACHE_PATH = DATA_DIR / "upcoming_odds.json"
FALLBACK_ODDS_CACHE_PATH = DATA_DIR / "odds_cache.json"

# Dictionnaire de traduction des 24 facteurs du modèle IA (EN / FR / ES)
FEATURE_LABELS_MAP = {
    "EN": {
        "delta_rank": "Official UFC Ranking Gap",
        "is_ranked_f1": "Fighter 1 Ranked in Top 15",
        "is_ranked_f2": "Fighter 2 Ranked in Top 15",
        "delta_Str_Acc": "Significant Strike Accuracy Gap (%)",
        "delta_SApM": "Strikes Absorbed Per Minute Gap",
        "delta_age": "Age Difference between Fighters",
        "delta_Str_Def": "Striking Defense Rate Gap (%)",
        "delta_TD_Def": "Takedown Defense Rate Gap (%)",
        "delta_SlpM": "Significant Strikes Landed / Min",
        "delta_ufc_win_rate": "Career UFC Win Rate Gap (%)",
        "delta_SlpM_3y": "3-Year Striking Output Trend",
        "delta_elo": "Dynamic ELO Rating Gap",
        "delta_TD_Acc": "Takedown Accuracy Gap (%)",
        "delta_Sub_Avg": "Submissions Attempted / 15 Min",
        "delta_TD_Def_3y": "3-Year Takedown Defense Trend",
        "delta_TD_Avg": "Takedowns Landed / 15 Min",
        "delta_win_rate_3y": "3-Year Recent Win Rate",
        "delta_SApM_3y": "3-Year Recent Damage Absorbed",
        "delta_win_streak": "Current Win Streak Gap",
        "delta_win_rate_last_5": "Recent Form (Last 5 Fights)",
        "delta_reach_cm": "Reach Advantage (cm)",
        "delta_ufc_fights": "UFC Octagon Experience Gap",
        "delta_loss_streak": "Current Loss Streak Gap",
        "delta_height_cm": "Height Advantage (cm)"
    },
    "FR": {
        "delta_rank": "Écart de Classement Officiel (Rank)",
        "is_ranked_f1": "Combattant 1 Classé Top 15",
        "is_ranked_f2": "Combattant 2 Classé Top 15",
        "delta_Str_Acc": "Précision des Coups Significatifs (%)",
        "delta_SApM": "Coups Absorbés / Min (Défense)",
        "delta_age": "Différence d'Âge entre Combattants",
        "delta_Str_Def": "Défense aux Coups Debout (%)",
        "delta_TD_Def": "Défense contre les Takedowns (%)",
        "delta_SlpM": "Coups Significatifs Connectés / Min",
        "delta_ufc_win_rate": "Taux de Victoire UFC en Carrière (%)",
        "delta_SlpM_3y": "Volume de Coups sur 3 Ans (Tendance)",
        "delta_elo": "Différentiel de Score ELO Dynamique",
        "delta_TD_Acc": "Précision des Takedowns Réussis (%)",
        "delta_Sub_Avg": "Tentatives de Soumission / 15 Min",
        "delta_TD_Def_3y": "Défense Takedown sur 3 Ans (Tendance)",
        "delta_TD_Avg": "Mises au Sol Réussies / 15 Min",
        "delta_win_rate_3y": "Taux de Victoire sur les 3 Dernières Années",
        "delta_SApM_3y": "Coups Absorbés sur 3 Ans (Usure Récente)",
        "delta_win_streak": "Écart de Série de Victoires en Cours",
        "delta_win_rate_last_5": "Forme Récente (5 Derniers Combats)",
        "delta_reach_cm": "Avantage d'Allonge (en cm)",
        "delta_ufc_fights": "Expérience dans l'Octogone UFC",
        "delta_loss_streak": "Écart de Série de Défaites en Cours",
        "delta_height_cm": "Avantage de Taille (en cm)"
    },
    "ES": {
        "delta_rank": "Diferencia de Ranking Oficial (UFC)",
        "is_ranked_f1": "Peleador 1 en el Top 15",
        "is_ranked_f2": "Peleador 2 en el Top 15",
        "delta_Str_Acc": "Precisión de Golpes Significativos (%)",
        "delta_SApM": "Golpes Absorbidos por Minuto (Defensa)",
        "delta_age": "Diferencia de Edad entre Peleadores",
        "delta_Str_Def": "Defensa de Golpes de Pie (%)",
        "delta_TD_Def": "Defensa de Derribos (%)",
        "delta_SlpM": "Golpes Significativos Conectados / Min",
        "delta_ufc_win_rate": "Porcentaje de Victorias en UFC (%)",
        "delta_SlpM_3y": "Volumen de Golpes en 3 Años (Tendencia)",
        "delta_elo": "Diferencia de Puntuación ELO Dinámica",
        "delta_TD_Acc": "Efectividad de Derribos (%)",
        "delta_Sub_Avg": "Intentos de Sumisión / 15 Min",
        "delta_TD_Def_3y": "Defensa de Derribo en 3 Años",
        "delta_TD_Avg": "Derribos Conectados / 15 Min",
        "delta_win_rate_3y": "Porcentaje de Victorias Reciente (3 Años)",
        "delta_SApM_3y": "Daño Absorbido en 3 Años (Desgaste)",
        "delta_win_streak": "Racha de Victorias Actual",
        "delta_win_rate_last_5": "Forma Reciente (Últimas 5 Peleas)",
        "delta_reach_cm": "Ventaja de Alcance (en cm)",
        "delta_ufc_fights": "Experiencia en el Octágono UFC",
        "delta_loss_streak": "Racha de Derrotas Actual",
        "delta_height_cm": "Ventaja de Estatura (en cm)"
    }
}


# Utilitaires légers natifs (zéro dépendance lourde au chargement)
try:
    from src.utils import normalize_fighter_name, fuzzy_match_fighter_name
except ImportError:
    from utils import normalize_fighter_name, fuzzy_match_fighter_name


def deduplicate_card_fights(fights):
    """Purge strictement tout combat en doublon sur une carte."""
    unique_fights = []
    seen_pairs = set()

    for f in fights:
        f1 = f.get("f1") or f.get("home_team", "")
        f2 = f.get("f2") or f.get("away_team", "")
        if not f1 or not f2:
            continue

        n1 = normalize_fighter_name(f1)
        n2 = normalize_fighter_name(f2)
        pair_key = tuple(sorted([n1, n2]))

        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_fights.append(f)
        else:
            for u in unique_fights:
                un1 = normalize_fighter_name(u.get("f1", ""))
                un2 = normalize_fighter_name(u.get("f2", ""))
                if tuple(sorted([un1, un2])) == pair_key:
                    if not u.get("winner") and f.get("winner"):
                        u["winner"] = f["winner"]
                    break

    return unique_fights


def deduplicate_upcoming_cards(cards_dict):
    """Fusionne les doublons d'événements à la même date en conservant le titre le plus complet."""
    date_to_key = {}
    deduped_cards = collections.OrderedDict()

    for key, card in cards_dict.items():
        date_str = card.get("event_date") or key.split("|")[0].strip()
        title = card.get("event_title") or key.split("|")[-1].strip()

        if date_str not in date_to_key:
            date_to_key[date_str] = key
            card["fights"] = deduplicate_card_fights(card.get("fights", []))
            deduped_cards[key] = card
        else:
            existing_key = date_to_key[date_str]
            existing_card = deduped_cards[existing_key]

            all_fights = existing_card.get("fights", []) + card.get("fights", [])
            existing_card["fights"] = deduplicate_card_fights(all_fights)

            existing_title = existing_card.get("event_title", "")
            if len(title) > len(existing_title):
                existing_card["event_title"] = title
                new_key = f"{date_str} | {title}"
                del deduped_cards[existing_key]
                deduped_cards[new_key] = existing_card
                date_to_key[date_str] = new_key

    return deduped_cards


def _ensure_backend_initialized():
    """Initialise le tracker local si le fichier n'existe pas encore sur le disque."""
    if not TRACKER_PATH.exists():
        try:
            from src.odds_api import get_cached_or_fresh_odds
            from src.predict import load_resources_v3
            from src.historical_tracker import sync_historical_tracker
        except ImportError:
            from odds_api import get_cached_or_fresh_odds
            from predict import load_resources_v3
            from historical_tracker import sync_historical_tracker

        events, _, _ = get_cached_or_fresh_odds(force_refresh=False)
        model, raw_df, medians, all_fighters, _ = load_resources_v3()
        sync_historical_tracker(events, raw_df, model, medians, all_fighters)


def get_all_cards_from_cache():
    """
    Lit le fichier local data/historical_tracker.json en mode passif strict.
    Retourne (upcoming_cards, past_cards_reversed, summary).
    """
    if not TRACKER_PATH.exists():
        _ensure_backend_initialized()

    try:
        with open(TRACKER_PATH, "r", encoding="utf-8") as f:
            tracker_data = json.load(f)
    except Exception as e:
        print(f"[!] Erreur de lecture de {TRACKER_PATH} ({e}).")
        return collections.OrderedDict(), collections.OrderedDict(), {}

    cards_map = tracker_data.get("cards", {})
    summary = tracker_data.get("summary", {})
    today_str = datetime.now().strftime("%Y-%m-%d")

    upcoming_cards = collections.OrderedDict()
    past_cards = collections.OrderedDict()

    for k in sorted(cards_map.keys()):
        c_info = cards_map[k]
        c_date = c_info.get("event_date", "")
        is_comp = c_info.get("is_completed", False)

        if is_comp or c_date < today_str:
            past_cards[k] = c_info
        else:
            upcoming_cards[k] = c_info

    past_cards_reversed = collections.OrderedDict(reversed(list(past_cards.items())))
    return deduplicate_upcoming_cards(upcoming_cards), past_cards_reversed, summary


def get_upcoming_cards():
    """Retourne l'ensemble des cartes UFC futures dédoublonnées avec pronostics pré-calculés."""
    upcoming, _, _ = get_all_cards_from_cache()
    return upcoming


def get_past_cards():
    """Retourne l'ensemble des cartes UFC passées (antichronologiques) sans data leakage."""
    _, past, _ = get_all_cards_from_cache()
    return past


def get_financial_summary():
    """Retourne le bilan financier consolidé (Profit, ROI, Win Rate, Précision globale)."""
    _, _, summary = get_all_cards_from_cache()
    return summary


def get_odds_metadata():
    """
    Retourne les métadonnées de fraîcheur des cotes :
    - age_mins : Âge en minutes
    - age_hours : Âge en heures
    - last_updated_utc : Timestamp ISO UTC
    - from_cache : Booléen
    """
    cache_path = ODDS_CACHE_PATH if ODDS_CACHE_PATH.exists() else FALLBACK_ODDS_CACHE_PATH
    current_time = datetime.now(timezone.utc).timestamp()

    if cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            last_utc_str = data.get("last_updated_utc")
            if last_utc_str:
                dt = datetime.fromisoformat(last_utc_str.replace("Z", "+00:00"))
                timestamp = dt.timestamp()
            else:
                timestamp = data.get("timestamp", current_time)

            age_hours = max(0.0, (current_time - timestamp) / 3600.0)
            age_mins = max(1, int(age_hours * 60))
            return {
                "age_mins": age_mins,
                "age_hours": age_hours,
                "last_updated_utc": last_utc_str or datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat(),
                "from_cache": True,
                "events_count": len(data.get("events", []))
            }
        except Exception:
            pass

    return {
        "age_mins": 1,
        "age_hours": 0.0,
        "last_updated_utc": datetime.now(timezone.utc).isoformat(),
        "from_cache": False,
        "events_count": 0
    }


def get_feature_importances(lang="EN"):
    """
    Extrait instantanément les pourcentages d'importance des variables du modèle IA (Total = 100%).
    Lit les métadonnées pré-calculées dans models/model_metadata_v3.json pour une réponse en < 1ms.
    Retourne une liste de tuples : [(col_name, label_traduit, pct), ...] triée par importance décroissante.
    """
    metadata_path = MODELS_DIR / "model_metadata_v3.json"
    feat_map = {}

    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            feat_map = meta.get("feature_importances", {})
        except Exception:
            pass

    if not feat_map:
        try:
            model, _, _, _, _ = load_resources_v3()
            if hasattr(model, "calibrated_classifiers_"):
                all_imps = [clf.estimator.feature_importances_ for clf in model.calibrated_classifiers_]
                mean_imps = np.mean(all_imps, axis=0)
            elif hasattr(model, "feature_importances_"):
                mean_imps = model.feature_importances_
            else:
                mean_imps = np.ones(len(FEATURE_COLS_V3))

            for col, imp in zip(FEATURE_COLS_V3, mean_imps):
                feat_map[col] = float(imp)
        except Exception:
            for col in FEATURE_COLS_V3:
                feat_map[col] = 1.0 / len(FEATURE_COLS_V3)

    total = sum(feat_map.values()) if sum(feat_map.values()) > 0 else 1.0
    sorted_items = sorted(feat_map.items(), key=lambda x: x[1], reverse=True)

    lang_map = FEATURE_LABELS_MAP.get(lang.upper(), FEATURE_LABELS_MAP["EN"])
    results = []
    for col, imp in sorted_items:
        pct = (imp / total) * 100.0
        label = lang_map.get(col, col)
        results.append((col, label, pct))

    return results


def run_background_sync(force_refresh=False):
    """
    Exécute le cycle complet d'orchestration backend (réservé aux tâches de fond / cron / warmup) :
    1. Mise à jour de The Odds API (1 seul appel HTTP batch, contrôlé par TTL).
    2. Récupération des cartes officielles ESPN.
    3. Inférence prédictive XGBoost V3.
    4. Synchronisation point-in-time du tracker et sauvegarde dans data/historical_tracker.json.
    """
    try:
        from src.odds_api import get_cached_or_fresh_odds
        from src.predict import load_resources_v3
        from src.historical_tracker import sync_historical_tracker
    except ImportError:
        from odds_api import get_cached_or_fresh_odds
        from predict import load_resources_v3
        from historical_tracker import sync_historical_tracker

    events, from_cache, age_hours = get_cached_or_fresh_odds(force_refresh=force_refresh)
    model, raw_df, medians, all_fighters, _ = load_resources_v3()
    upcoming, past, summary = sync_historical_tracker(events, raw_df, model, medians, all_fighters)
    return {
        "upcoming_count": len(upcoming),
        "past_count": len(past),
        "from_cache": from_cache,
        "age_hours": age_hours,
        "summary": summary
    }
