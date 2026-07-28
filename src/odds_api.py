"""
Module de gestion et de récupération des cotes en temps réel via The Odds API.
Pipeline générique multi-événements avec stratégie Cache-First (2h) et 1 seul appel API batch global.
Croisement hybride avec UFCStats, filtrage temporel (date >= aujourd'hui) et tri chronologique.
"""

import os
import sys
import json
import time
from datetime import datetime, timezone
import requests
from dotenv import load_dotenv

# Utilitaires de normalisation et matching
try:
    from src.utils import normalize_fighter_name, fuzzy_match_fighter_name, is_token_set_match
except ImportError:
    from utils import normalize_fighter_name, fuzzy_match_fighter_name, is_token_set_match

load_dotenv()

CACHE_FILE_PATH = os.path.join("data", "odds_cache.json")
CACHE_DURATION_SECONDS = 2 * 3600  # 2 heures en secondes
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds/"
OFFICIAL_UFC_API_URL = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"


def get_official_ufc_cards():
    """
    Scrape et récupère l'intégralité des soirées UFC officielles FUTURES (date >= aujourd'hui),
    triées par ordre chronologique croissant (de la carte la plus proche à la plus lointaine),
    avec leurs combats ordonnés du Main Event jusqu'aux préliminaires.
    """
    official_cards = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    today_str = time.strftime("%Y-%m-%d")
    start_d = today_str.replace("-", "")
    current_year = time.strftime("%Y")

    try:
        url = f"{OFFICIAL_UFC_API_URL}?dates={start_d}-{current_year}1231"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            events_data = data.get("events", [])

            for ev in events_data:
                event_id = ev.get("id", "")
                event_name = ev.get("name", "UFC Event")
                event_date = ev.get("date", "")[:10]

                # Filtre temporel strict : Ignorer les événements passés ou hors UFC
                if event_date < today_str or "UFC" not in event_name.upper():
                    continue

                competitions = ev.get("competitions", [])

                # Inverser la liste des combats pour placer le Main Event en position 0
                comps_reversed = list(reversed(competitions))
                card_fights = []

                for fight_idx, comp in enumerate(comps_reversed):
                    comps = comp.get("competitors", [])
                    if len(comps) >= 2:
                        f1_name = comps[0].get("athlete", {}).get("displayName", "")
                        f2_name = comps[1].get("athlete", {}).get("displayName", "")
                        if f1_name and f2_name:
                            label = "MAIN EVENT" if fight_idx == 0 else ("CO-MAIN EVENT" if fight_idx == 1 else f"Combat #{fight_idx + 1}")
                            card_fights.append({
                                "fight_index": fight_idx,
                                "fight_label": label,
                                "f1": f1_name,
                                "f2": f2_name,
                                "norm_f1": normalize_fighter_name(f1_name),
                                "norm_f2": normalize_fighter_name(f2_name)
                            })

                if card_fights:
                    official_cards.append({
                        "event_id": event_id,
                        "event_name": event_name,
                        "event_date": event_date,
                        "fights": card_fights
                    })
    except Exception as e:
        print(f"[!] Avertissement : Impossible de récupérer les cartes officielles UFC ({e}).")

    # Tri Chronologique Croissant (de la carte la plus proche à la plus lointaine)
    official_cards = sorted(official_cards, key=lambda x: x["event_date"])
    return official_cards


def match_odds_to_fight(f1: str, f2: str, raw_odds_events: list) -> list:
    """Recherche les cotes bookmakers dans The Odds API pour un duel (f1 vs f2)."""
    if not raw_odds_events:
        return []

    for ev in raw_odds_events:
        h = ev.get("home_team", "")
        a = ev.get("away_team", "")

        m1_h = fuzzy_match_fighter_name(f1, [h], threshold=0.70)
        m2_a = fuzzy_match_fighter_name(f2, [a], threshold=0.70)
        m1_a = fuzzy_match_fighter_name(f1, [a], threshold=0.70)
        m2_h = fuzzy_match_fighter_name(f2, [h], threshold=0.70)

        if (m1_h and m2_a) or (m1_a and m2_h):
            bookmakers = json.loads(json.dumps(ev.get("bookmakers", [])))
            for bkm in bookmakers:
                for mkt in bkm.get("markets", []):
                    if mkt.get("key") == "h2h":
                        for outcome in mkt.get("outcomes", []):
                            oname = outcome.get("name", "")
                            if fuzzy_match_fighter_name(oname, [f1], threshold=0.70):
                                outcome["name"] = f1
                            elif fuzzy_match_fighter_name(oname, [f2], threshold=0.70):
                                outcome["name"] = f2
            return bookmakers

    return []


def get_cached_or_fresh_odds(force_refresh=False):
    """
    STRATÉGIE SERVEUR PASSIF / CLIENT SANS AUCUN APPEL RÉSEAU :
    1. Si not force_refresh -> Lire STRICTEMENT et EXCLUSIVEMENT le fichier local data/upcoming_odds.json / data/odds_cache.json (0 appel réseau client).
    2. Si force_refresh=True (tâche de fond / cron / warmup) -> Effectuer 1 SEUL appel API batch à The Odds API et mettre à jour le cache local avec last_updated_utc.
    """
    current_time = time.time()
    cache_file_primary = os.path.join("data", "upcoming_odds.json")
    cache_file_secondary = CACHE_FILE_PATH

    target_cache_path = cache_file_primary if os.path.exists(cache_file_primary) else cache_file_secondary

    # 1. Mode Client Passif (not force_refresh) : 0 appel réseau
    if not force_refresh and os.path.exists(target_cache_path):
        try:
            with open(target_cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            last_utc_str = cache_data.get("last_updated_utc")
            if last_utc_str:
                try:
                    dt = datetime.fromisoformat(last_utc_str.replace("Z", "+00:00"))
                    timestamp = dt.timestamp()
                except Exception:
                    timestamp = cache_data.get("timestamp", current_time)
            else:
                timestamp = cache_data.get("timestamp", current_time)

            age_hours = (current_time - timestamp) / 3600.0
            if "events" in cache_data and len(cache_data["events"]) > 0:
                return cache_data["events"], True, max(0.0, age_hours)
        except Exception as e:
            print(f"[!] Erreur de lecture du cache local ({e}).")

    # Si le fichier local n'existe pas du tout et force_refresh est False, essayer le fichier secondaire
    if not force_refresh and os.path.exists(cache_file_secondary):
        try:
            with open(cache_file_secondary, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            timestamp = cache_data.get("timestamp", current_time)
            age_hours = (current_time - timestamp) / 3600.0
            if "events" in cache_data:
                return cache_data["events"], True, max(0.0, age_hours)
        except Exception:
            pass

    # 2. Mode Rafraîchissement Arrière-Plan (force_refresh=True)
    api_key = os.getenv("ODDS_API_KEY")
    if not api_key or api_key.strip() == "votre_cle_api_ici":
        print("\n[!] Clé ODDS_API_KEY non configurée dans le fichier .env.")
        return None, False, 0.0

    params = {
        "apiKey": api_key.strip(),
        "regions": "eu,us",
        "markets": "h2h",
        "oddsFormat": "decimal"
    }

    try:
        print("   [+] Rafraîchissement des cotes : 1 SEUL appel API batch global vers The Odds API...")
        response = requests.get(ODDS_API_URL, params=params, timeout=10)

        raw_odds_events = response.json() if response.status_code == 200 else []

        # 3. Récupération de l'index des cartes UFC futures et croisement
        print("   [+] Croisement Multi-Événements : Cartes UFC officielles futures...")
        official_cards = get_official_ufc_cards()

        all_processed_events = []
        matched_fights_count = 0

        for card in official_cards:
            event_name = card["event_name"]
            event_date = card["event_date"]
            fights = card["fights"]

            for fight in fights:
                f1 = fight["f1"]
                f2 = fight["f2"]
                fight_idx = fight["fight_index"]
                fight_label = fight["fight_label"]

                # Recherche des cotes avec matching tolérant
                bkm_list = match_odds_to_fight(f1, f2, raw_odds_events)
                if bkm_list:
                    matched_fights_count += 1

                all_processed_events.append({
                    "event_title": event_name,
                    "commence_time": f"{event_date}T00:00:00Z",
                    "event_date": event_date,
                    "home_team": f1,
                    "away_team": f2,
                    "fight_index": fight_idx,
                    "fight_label": fight_label,
                    "bookmakers": bkm_list
                })

        print(f"   [+] Pipeline V3 terminé : {len(official_cards)} cartes UFC futures ({len(all_processed_events)} combats, {matched_fights_count} cotes réelles).")

        now_utc = datetime.now(timezone.utc)
        cache_to_save = {
            "timestamp": current_time,
            "last_updated_utc": now_utc.isoformat(),
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(current_time)),
            "cards_count": len(official_cards),
            "events_count": len(all_processed_events),
            "events": all_processed_events
        }

        for save_path in [cache_file_primary, cache_file_secondary]:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(cache_to_save, f, indent=4)

        return all_processed_events, False, 0.0

    except Exception as e:
        print(f"\n[!] Impossible de contacter The Odds API : {e}")
        if os.path.exists(cache_file_primary):
            with open(cache_file_primary, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            return cache_data.get("events", None), True, 999.0
        elif os.path.exists(cache_file_secondary):
            with open(cache_file_secondary, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            return cache_data.get("events", None), True, 999.0
        return None, False, 0.0


def get_odds_for_match(fighter_1, fighter_2):
    """
    Recherche les cotes d'un duel (fighter_1 vs fighter_2) dans le cache assaini.
    Retourne un dictionnaire avec odds_f1, odds_f2, bookmaker, from_cache ou None.
    """
    events, from_cache, age_hours = get_cached_or_fresh_odds()
    if not events:
        return None

    event_fighters = []
    for ev in events:
        h = ev.get("home_team", "")
        a = ev.get("away_team", "")
        if h: event_fighters.append(h)
        if a: event_fighters.append(a)

    matched_f1 = fuzzy_match_fighter_name(fighter_1, event_fighters, threshold=0.75)
    matched_f2 = fuzzy_match_fighter_name(fighter_2, event_fighters, threshold=0.75)

    if not matched_f1 or not matched_f2:
        return None

    target_event = None
    for ev in events:
        h = ev.get("home_team", "")
        a = ev.get("away_team", "")
        if (h == matched_f1 and a == matched_f2) or (h == matched_f2 and a == matched_f1):
            target_event = ev
            break

    if not target_event or "bookmakers" not in target_event:
        return None

    bookmakers = target_event.get("bookmakers", [])
    if not bookmakers:
        return None

    odds_f1_best = None
    odds_f2_best = None
    chosen_bookmaker = None

    for bkm in bookmakers:
        name_bkm = bkm.get("title", bkm.get("key", "Bookmaker"))
        markets = bkm.get("markets", [])
        for mkt in markets:
            if mkt.get("key") == "h2h":
                outcomes = mkt.get("outcomes", [])
                odds_map = {o["name"]: float(o["price"]) for o in outcomes if "name" in o and "price" in o}

                o_f1 = odds_map.get(matched_f1)
                o_f2 = odds_map.get(matched_f2)

                if o_f1 and o_f2:
                    if odds_f1_best is None or (o_f1 + o_f2 > odds_f1_best + odds_f2_best):
                        odds_f1_best = o_f1
                        odds_f2_best = o_f2
                        chosen_bookmaker = name_bkm

    if odds_f1_best and odds_f2_best:
        return {
            "odds_f1": odds_f1_best,
            "odds_f2": odds_f2_best,
            "bookmaker": chosen_bookmaker,
            "from_cache": from_cache,
            "cache_age_hours": age_hours,
            "match_title": f"{matched_f1} vs {matched_f2}"
        }

    return None
