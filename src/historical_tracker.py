"""
Module d'archivage automatique, de suivi financier et d'historique de performance (Baseline 19 Juillet 2026).
Gère la persistance dans data/historical_tracker.json, le gel (freeze) des pronostics avant événement,
la récupération automatique des vainqueurs officiels d'UFCStats/ESPN,
la purge des doublons et la bascule automatique des cartes "futures" vers "passées" avec le bilan cumulé (Mise fixe 10 €).
"""

import os
import sys
import json
import time
import collections
import requests
import numpy as np
import pandas as pd

try:
    from src.utils import normalize_fighter_name, fuzzy_match_fighter_name
    from src.predict import (
        resolve_fighter_name, compute_fighter_dynamic_states_v3,
        get_latest_fighter_profile_v3, STAT_COLS_V1, FEATURE_COLS_V3
    )
except ImportError:
    from utils import normalize_fighter_name, fuzzy_match_fighter_name
    from predict import (
        resolve_fighter_name, compute_fighter_dynamic_states_v3,
        get_latest_fighter_profile_v3, STAT_COLS_V1, FEATURE_COLS_V3
    )

TRACKER_FILE_PATH = os.path.join("data", "historical_tracker.json")
BASELINE_DATE = "2026-05-09"  # Baseline officielle incluant 10 cartes passées (du 9 Mai 2026 au 25 Juillet 2026)
OFFICIAL_UFC_API_URL = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"

HISTORICAL_CLOSING_ODDS = {
    # Card 1: 2026-05-09 | UFC 328: Chimaev vs. Strickland
    ("Khamzat Chimaev", "Sean Strickland"): (1.25, 4.00),
    ("Tatsuro Taira", "Joshua Van"): (1.50, 2.70),
    ("Alexander Volkov", "Waldo Cortes Acosta"): (1.60, 2.40),
    ("Joaquin Buckley", "Sean Brady"): (2.20, 1.70),
    ("Jeremy Stephens", "King Green"): (2.50, 1.55),
    ("Ozzy Diaz", "Ateba Gautier"): (2.10, 1.75),
    ("Yaroslav Amosov", "Joel Álvarez"): (1.70, 2.20),
    ("Grant Dawson", "Mateusz Rębecki"): (1.45, 2.85),
    ("Jim Miller", "Jared Gordon"): (2.30, 1.65),
    ("Roman Kopylov", "Marco Tulio"): (1.75, 2.10),
    ("Pat Sabatini", "William Gomis"): (1.80, 2.05),
    ("Djorden Santos", "Baisangur Susurkaev"): (2.40, 1.60),
    ("Clayton Carpenter", "Jose Ochoa"): (1.57, 2.50),

    # Card 2: 2026-05-16 | UFC Fight Night: Allen vs. Costa
    ("Arnold Allen", "Melquizael Costa"): (1.40, 3.00),
    ("Dooho Choi", "Daniel Santos"): (1.72, 2.15),
    ("Malcolm Wellmaker", "Juan Diaz"): (1.85, 1.95),
    ("Modestas Bukauskas", "Christian Edwards"): (1.65, 2.30),
    ("Bernardo Sopaj", "Timmy Cuamba"): (1.70, 2.20),
    ("Khaos Williams", "Nikolay Veretennikov"): (1.60, 2.40),
    ("Tuco Tokkos", "Ivan Erslan"): (2.25, 1.67),
    ("Tommy Gantt", "Artur Minev"): (1.80, 2.05),
    ("Ketlen Vieira", "Jacqueline Cavalcanti"): (1.75, 2.10),
    ("Cody Brundage", "Andre Petroski"): (2.10, 1.75),
    ("Alice Ardelean", "Polyana Viana"): (1.90, 1.90),
    ("Daniel Barez", "Luis Gurule"): (2.00, 1.80),
    ("Nicolle Caliari", "Shauna Bannon"): (1.65, 2.30),

    # Card 3: 2026-05-30 | UFC Fight Night: Song vs. Figueiredo
    ("Song Yadong", "Deiveson Figueiredo"): (1.53, 2.60),
    ("Alonzo Menifield", "Zhang Mingyang"): (2.30, 1.65),
    ("Sergei Pavlovich", "Tallison Teixeira"): (1.36, 3.25),
    ("Kai Asakura", "Cameron Smotherman"): (1.45, 2.85),
    ("Jake Matthews", "Carlston Harris"): (1.70, 2.20),
    ("Alex Perez", "Sumudaerji"): (1.60, 2.40),
    ("Luis Felipe Dias", "Yi Sak Lee"): (1.75, 2.10),
    ("Ding Meng", "Jose Henrique"): (2.05, 1.80),
    ("Aoriqileng", "Cody Haddon"): (2.20, 1.70),
    ("Rei Tsuruya", "Luis Gurule"): (1.30, 3.60),
    ("Angela Hill", "Jingnan Xiong"): (1.65, 2.30),
    ("Rodrigo Vera", "Zhu Kangjie"): (1.85, 1.95),
    ("Loma Lookboonmee", "Jaqueline Amorim"): (2.10, 1.75),

    # Card 4: 2026-06-06 | UFC Fight Night: Muhammad vs. Bonfim
    ("Belal Muhammad", "Gabriel Bonfim"): (1.67, 2.25),
    ("Brendan Allen", "Edmen Shahbazyan"): (1.50, 2.70),
    ("Farés Ziam", "Tom Nolan"): (1.90, 1.90),
    ("Bryce Mitchell", "Santiago Luna"): (1.33, 3.40),
    ("Junior Tafa", "Iwo Baraniewski"): (2.05, 1.80),
    ("Matt Schnell", "Alessandro Costa"): (2.40, 1.60),
    ("Marcus McGhee", "John Yannis"): (1.40, 3.00),
    ("Bruno Silva", "Édgar Cháirez"): (2.15, 1.72),
    ("Priscila Cachoeira", "Chelsea Chandler"): (2.50, 1.55),
    ("Joanderson Brito", "Jordan Leavitt"): (1.36, 3.25),
    ("Yuneisy Duben", "Jeisla Chaves"): (2.20, 1.70),
    ("Ariane Carnelossi", "Ketlen Souza"): (2.10, 1.75),

    # Card 5: 2026-06-15 | UFC Freedom 250: Topuria vs. Gaethje
    ("Ilia Topuria", "Justin Gaethje"): (1.22, 4.50),
    ("Ciryl Gane", "Alex Pereira"): (1.65, 2.30),
    ("Aiemann Zahabi", "Sean O'Malley"): (3.50, 1.30),
    ("Derrick Lewis", "Josh Hokit"): (2.60, 1.53),
    ("Michael Chandler", "Mauricio Ruffy"): (2.85, 1.45),
    ("Kyle Daukaus", "Bo Nickal"): (3.80, 1.26),
    ("Steve Garcia", "Diego Lopes"): (2.70, 1.50),

    # Card 6: 2026-06-20 | UFC Fight Night: Kape vs. Horiguchi 2
    ("Manel Kape", "Kyoji Horiguchi"): (1.53, 2.60),
    ("Ion Cutelaba", "Navajo Stirling"): (1.65, 2.30),
    ("Christian Rodriguez", "Hyder Amil"): (1.80, 2.05),
    ("Melsik Baghdasaryan", "Murtazali Magomedov"): (1.90, 1.90),
    ("Andre Fili", "Vinicius Oliveira"): (2.10, 1.75),
    ("Kevin Borjas", "Andre Lima"): (2.30, 1.65),
    ("Melissa Mullins", "Bia Mesquita"): (1.72, 2.15),
    ("Allan Nascimento", "Mitch Raposo"): (1.60, 2.40),
    ("Gaston Bolaños", "Michael Aswell"): (1.85, 1.95),
    ("Leon Shahbazyan", "Levan Chokheli"): (2.20, 1.70),
    ("Karol Rosa", "Luana Santos"): (1.55, 2.50),
    ("Otari Tanzilovi", "Shane Collins"): (1.80, 2.05),

    # Card 7: 2026-06-27 | UFC Fight Night: Fiziev vs. Torres
    ("Rafael Fiziev", "Manuel Torres"): (1.50, 2.70),
    ("Michel Pereira", "Shara Magomedov"): (1.91, 1.91),
    ("Nazim Sadykhov", "Matheus Camilo"): (1.62, 2.40),
    ("Asu Almabayev", "Charles Johnson"): (1.45, 2.85),
    ("Ikram Aliskerov", "Brunno Ferreira"): (1.40, 3.00),
    ("Abus Magomedov", "Michal Oleksiejczuk"): (1.75, 2.10),
    ("Eric Nolan", "Farman Hasanov"): (2.40, 1.60),
    ("Julius Walker", "Abdul-Rakhman Yakhyaev"): (2.10, 1.75),
    ("Nursulton Ruziboev", "Andrey Pulyaev"): (1.57, 2.50),
    ("Javier Reyes", "Kaan Ofli"): (2.25, 1.67),
    ("Theodor Berggren", "Daniil Donchenko"): (1.90, 1.90),
    ("Jean Matsumoto", "Bekzat Almakhan"): (1.70, 2.20),
    ("Tahir Abdullayev", "Jefferson Nascimento"): (1.80, 2.05),

    # Card 8: 2026-07-11 | UFC 329: McGregor vs. Holloway 2
    ("Max Holloway", "Conor McGregor"): (1.57, 2.50),
    ("Paddy Pimblett", "Benoit Saint Denis"): (1.80, 2.05),
    ("Cory Sandhagen", "Mario Bautista"): (1.72, 2.15),
    ("Brandon Royval", "Lone'er Kavanagh"): (1.65, 2.30),
    ("King Green", "Terrance McKinney"): (1.75, 2.10),
    ("Robert Whittaker", "Nikita Krylov"): (1.60, 2.40),
    ("Gable Steveson", "Elisha Ellison"): (1.15, 5.50),
    ("Cody Garbrandt", "Adrian Yañez"): (2.40, 1.60),
    ("Kai Kamaka III", "Luke Riley"): (2.10, 1.75),
    ("Wang Cong", "Tracy Cortez"): (1.50, 2.70),
    ("Cesar Almeida", "Damian Pinas"): (1.85, 1.95),
    ("Farid Basharat", "John Garza"): (1.25, 4.00),
    ("Zach Reese", "Ryan Gandra"): (1.67, 2.25),
    ("Cody Durden", "Alessandro Costa"): (2.20, 1.70),

    # Card 9: 2026-07-18 | UFC Fight Night: Du Plessis vs. Usman
    ("Dricus Du Plessis", "Kamaru Usman"): (1.43, 2.80),
    ("Christian Leroy Duncan", "Jared Cannonier"): (1.29, 3.70),
    ("Chase Hooper", "Mitch Ramirez"): (1.26, 3.80),
    ("Fatima Kline", "Tabatha Ricci"): (1.20, 4.50),
    ("Tommy McMillen", "Alberto Montes"): (1.50, 2.55),
    ("Jose Miguel Delgado", "Austin Bashi"): (2.15, 1.69),
    ("Jean-Paul Lebosnoyani", "Seokhyeon Ko"): (2.50, 1.53),
    ("Felipe Franco", "Levi Rodrigues Jr."): (2.25, 1.63),
    ("Ezra Elliott", "Damien Anderson"): (2.05, 1.74),
    ("Alden Coria", "Stewart Nicoll"): (1.08, 7.75),
    ("RJ Harris", "Alvin Hines"): (2.00, 1.80),
    ("Dione Barbosa", "Anna Melisano"): (1.15, 5.25),

    # Card 10: 2026-07-25 | UFC Fight Night: Ankalaev vs. Guskov
    ("Magomed Ankalaev", "Bogdan Guskov"): (1.19, 5.50),
    ("Ramazan Temirov", "Steve Erceg"): (1.87, 2.00),
    ("Wellington Turman", "Islam Dulatov"): (8.50, 1.08),
    ("Magomed Zaynukov", "Damian Rzepecki"): (1.28, 3.80),
    ("Rizvan Kuniev", "Tyrell Fortune"): (1.30, 3.75),
    ("Abubakar Vagaev", "Saygid Izagakhmaev"): (1.37, 3.30),
    ("Thomas Petersen", "Valter Walker"): (2.58, 1.59),
    ("Dustin Jacoby", "Muhammad Said"): (1.59, 2.45),
    ("Santiago Ponzinibbio", "Sam Patterson"): (4.85, 1.20),
    ("Ismael Bonfim", "Axel Sola"): (2.72, 1.50),
    ("Brendson Ribeiro", "Magomed Tuchalov"): (8.00, 1.10),
    ("Mike Davis", "Nurullo Aliev"): (3.00, 1.41),
    ("Cody Gibson", "Abdul Hussein"): (5.00, 1.18)
}


def get_historical_closing_odds(f1_raw, f2_raw):
    """Recherche les cotes de fermeture officielles dans le dictionnaire historique."""
    for (o1, o2), odds in HISTORICAL_CLOSING_ODDS.items():
        m1_dir = fuzzy_match_fighter_name(f1_raw, [o1], threshold=0.70)
        m2_dir = fuzzy_match_fighter_name(f2_raw, [o2], threshold=0.70)
        if m1_dir and m2_dir:
            return odds

        m1_rev = fuzzy_match_fighter_name(f1_raw, [o2], threshold=0.70)
        m2_rev = fuzzy_match_fighter_name(f2_raw, [o1], threshold=0.70)
        if m1_rev and m2_rev:
            return (odds[1], odds[0])
    return None, None


def load_historical_tracker():
    """Charge le fichier local historical_tracker.json."""
    if os.path.exists(TRACKER_FILE_PATH):
        try:
            with open(TRACKER_FILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"cards": {}, "last_updated": ""}


def save_historical_tracker(data):
    """Sauvegarde le fichier local historical_tracker.json."""
    os.makedirs(os.path.dirname(TRACKER_FILE_PATH), exist_ok=True)
    data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(TRACKER_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def fetch_past_completed_events():
    """
    Récupère sur l'API officielle ESPN/UFCStats les soirées UFC terminées depuis la date baseline (2026-07-18).
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    today_str = time.strftime("%Y-%m-%d")
    start_d = BASELINE_DATE.replace("-", "")
    end_d = today_str.replace("-", "")

    past_cards = []
    try:
        url = f"{OFFICIAL_UFC_API_URL}?dates={start_d}-{end_d}"
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            events_data = res.json().get("events", [])
            for ev in events_data:
                event_name = ev.get("name", "UFC Event")
                event_date = ev.get("date", "")[:10]
                status_state = ev.get("status", {}).get("type", {}).get("state", "")

                if "UFC" not in event_name.upper():
                    continue

                competitions = ev.get("competitions", [])
                comps_reversed = list(reversed(competitions))
                card_fights = []

                for fight_idx, comp in enumerate(comps_reversed):
                    comps = comp.get("competitors", [])
                    if len(comps) >= 2:
                        c1, c2 = comps[0], comps[1]
                        f1_name = c1.get("athlete", {}).get("displayName", "")
                        f2_name = c2.get("athlete", {}).get("displayName", "")
                        w1 = c1.get("winner", False)
                        w2 = c2.get("winner", False)

                        winner_name = f1_name if w1 else (f2_name if w2 else ("Draw/NC" if (status_state == "post") else None))

                        if f1_name and f2_name:
                            label = "MAIN EVENT" if fight_idx == 0 else ("CO-MAIN EVENT" if fight_idx == 1 else f"Combat #{fight_idx + 1}")
                            card_fights.append({
                                "fight_index": fight_idx,
                                "fight_label": label,
                                "f1": f1_name,
                                "f2": f2_name,
                                "winner": winner_name
                            })

                if card_fights:
                    past_cards.append({
                        "event_name": event_name,
                        "event_date": event_date,
                        "is_completed": (status_state == "post" or event_date < today_str),
                        "fights": card_fights
                    })
    except Exception as e:
        print(f"[!] Avertissement : Impossible de récupérer l'historique des cartes passées ({e}).")

    return past_cards


def deduplicate_card_fights(fights):
    """Purge strictly tout doublon au sein d'une carte en conservant le premier combat valide."""
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
    """
    Dédouble les cartes à venir en fusionnant les événements ayant la même date.
    Conserve le titre le plus complet et fusionne les combats sans doublons.
    """
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


def sync_historical_tracker(cache_events, raw_df, model, medians, all_fighters):
    """
    Synchronise et calcule le bilan financier cumulé :
    1. Gèle (freeze) les pronostics et cotes pour les cartes futures.
    2. Récupère les vainqueurs officiels d'UFCStats pour les cartes terminées.
    3. Purge automatiquement les doublons.
    4. Calcule les sous-motifs explicites de NO BET (Insuffisance données, Absence cotes, EV insuffisante).
    5. Calcule le bilan financier (Profit, ROI %, Win Rate %, Volume).
    """
    tracker_data = load_historical_tracker()
    cards_map = tracker_data.get("cards", {})

    elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict = compute_fighter_dynamic_states_v3(raw_df)

    # 1. Mise à jour / Gèle (freeze) des pronostics des combats depuis cache_events
    if cache_events:
        for ev in cache_events:
            title = ev.get("event_title", "UFC Event")
            dt_str = ev.get("event_date", ev.get("commence_time", "")[:10])
            card_key = f"{dt_str} | {title}"

            if card_key not in cards_map:
                cards_map[card_key] = {
                    "event_title": title,
                    "event_date": dt_str,
                    "is_completed": False,
                    "fights": []
                }

            f1_raw = ev.get("home_team", "")
            f2_raw = ev.get("away_team", "")
            fight_idx = ev.get("fight_index", 0)
            fight_label = ev.get("fight_label", f"Combat #{fight_idx + 1}")
            bookmakers = ev.get("bookmakers", [])

            name_a = resolve_fighter_name(f1_raw, all_fighters)
            name_b = resolve_fighter_name(f2_raw, all_fighters)

            odds_a, odds_b, bkm_name = None, None, None
            targets = [t for t in [name_a, name_b, f1_raw, f2_raw] if t]

            for bkm in bookmakers:
                bname = bkm.get("title", bkm.get("key", "Bookmaker"))
                for mkt in bkm.get("markets", []):
                    if mkt.get("key") == "h2h":
                        outcomes = mkt.get("outcomes", [])
                        omap = {}
                        for o in outcomes:
                            oname = o.get("name", "")
                            oprice = float(o.get("price", 0.0))
                            if oname and oprice > 1.0:
                                matched = fuzzy_match_fighter_name(oname, targets, threshold=0.70)
                                if matched:
                                    omap[matched] = oprice

                        o_a = omap.get(name_a) or omap.get(f1_raw)
                        o_b = omap.get(name_b) or omap.get(f2_raw)

                        if o_a and o_b:
                            if odds_a is None or (o_a + o_b > odds_a + odds_b):
                                odds_a, odds_b, bkm_name = o_a, o_b, bname

            profile_a = get_latest_fighter_profile_v3(name_a, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if name_a else None
            profile_b = get_latest_fighter_profile_v3(name_b, raw_df, elo_dict, history_dict, win_streak_dict, loss_streak_dict, latest_rank_dict) if name_a else None

            has_full_data = bool(name_a and name_b and profile_a is not None and profile_b is not None)
            has_valid_odds = bool(odds_a and odds_b and odds_a > 1.0 and odds_b > 1.0)

            pct_a, pct_b = None, None
            ev_a, ev_b = None, None
            is_value_bet = False
            bet_fighter = None
            bet_odds = None
            bet_prob = None
            no_bet_reason = None
            max_ev_pct = None

            if has_full_data:
                delta_dict = {}
                for stat in STAT_COLS_V1:
                    delta_key = f"delta_{stat}"
                    val_a, val_b = profile_a[stat], profile_b[stat]
                    delta_dict[delta_key] = (val_a - val_b) if (pd.notna(val_a) and pd.notna(val_b)) else medians.get(delta_key, 0.0)

                delta_dict["delta_elo"] = profile_a["elo"] - profile_b["elo"]
                delta_dict["delta_win_streak"] = profile_a["win_streak"] - profile_b["win_streak"]
                delta_dict["delta_loss_streak"] = profile_a["loss_streak"] - profile_b["loss_streak"]
                delta_dict["delta_win_rate_last_5"] = profile_a["win_rate_5"] - profile_b["win_rate_5"]
                delta_dict["delta_ufc_win_rate"] = profile_a["ufc_win_rate"] - profile_b["ufc_win_rate"]
                delta_dict["delta_ufc_fights"] = profile_a["ufc_fights"] - profile_b["ufc_fights"]
                delta_dict["delta_rank"] = profile_b["rank"] - profile_a["rank"]
                delta_dict["is_ranked_f1"] = profile_a["is_ranked"]
                delta_dict["is_ranked_f2"] = profile_b["is_ranked"]
                delta_dict["delta_win_rate_3y"] = profile_a["wr_3y"] - profile_b["wr_3y"]
                delta_dict["delta_SlpM_3y"] = (profile_a["slpm_3y"] - profile_b["slpm_3y"]) if (pd.notna(profile_a["slpm_3y"]) and pd.notna(profile_b["slpm_3y"])) else medians.get("delta_SlpM_3y", 0.0)
                delta_dict["delta_SApM_3y"] = (profile_a["sapm_3y"] - profile_b["sapm_3y"]) if (pd.notna(profile_a["sapm_3y"]) and pd.notna(profile_b["sapm_3y"])) else medians.get("delta_SApM_3y", 0.0)
                delta_dict["delta_TD_Def_3y"] = (profile_a["td_def_3y"] - profile_b["td_def_3y"]) if (pd.notna(profile_a["td_def_3y"]) and pd.notna(profile_b["td_def_3y"])) else medians.get("delta_TD_Def_3y", 0.0)

                X_input = pd.DataFrame([delta_dict])[FEATURE_COLS_V3]
                probs = model.predict_proba(X_input)[0]
                prob_b_loss, prob_a_win = probs[0], probs[1]
                pct_a = float(prob_a_win * 100.0)
                pct_b = float(prob_b_loss * 100.0)

                if has_valid_odds:
                    ev_a = float((prob_a_win * odds_a) - 1.0)
                    ev_b = float((prob_b_loss * odds_b) - 1.0)
                    best_ev = max(ev_a, ev_b)
                    max_ev_pct = float(best_ev * 100.0)

                    if best_ev > 0.20:
                        is_value_bet = True
                        bet_fighter = f1_raw if ev_a >= ev_b else f2_raw
                        bet_odds = odds_a if ev_a >= ev_b else odds_b
                        bet_prob = float(prob_a_win if ev_a >= ev_b else prob_b_loss)
                    else:
                        no_bet_reason = "NO_BET_LOW_EV"
                else:
                    no_bet_reason = "NO_BET_NO_ODDS"
            else:
                no_bet_reason = "NO_BET_MISSING_DATA"

            existing_fights = cards_map[card_key].get("fights", [])
            fight_found = False

            n1_req = normalize_fighter_name(f1_raw)
            n2_req = normalize_fighter_name(f2_raw)
            req_pair = tuple(sorted([n1_req, n2_req]))

            for ex in existing_fights:
                ex_n1 = normalize_fighter_name(ex.get("f1", ""))
                ex_n2 = normalize_fighter_name(ex.get("f2", ""))
                if tuple(sorted([ex_n1, ex_n2])) == req_pair:
                    fight_found = True
                    ex["bookmakers"] = bookmakers
                    if not ex.get("has_valid_odds") and has_valid_odds:
                        ex["odds_a"] = odds_a
                        ex["odds_b"] = odds_b
                        ex["bkm_name"] = bkm_name
                        ex["has_valid_odds"] = True
                        ex["ev_a"] = ev_a
                        ex["ev_b"] = ev_b
                        ex["is_value_bet"] = is_value_bet
                        ex["bet_fighter"] = bet_fighter
                        ex["bet_odds"] = bet_odds
                        ex["bet_prob"] = bet_prob
                        ex["no_bet_reason"] = no_bet_reason
                        ex["max_ev_pct"] = max_ev_pct
                    break

            if not fight_found:
                existing_fights.append({
                    "fight_index": fight_idx,
                    "fight_label": fight_label,
                    "f1": f1_raw,
                    "f2": f2_raw,
                    "bookmakers": bookmakers,
                    "has_full_data": has_full_data,
                    "has_valid_odds": has_valid_odds,
                    "pct_a": pct_a,
                    "pct_b": pct_b,
                    "odds_a": odds_a,
                    "odds_b": odds_b,
                    "bkm_name": bkm_name,
                    "ev_a": ev_a,
                    "ev_b": ev_b,
                    "is_value_bet": is_value_bet,
                    "bet_fighter": bet_fighter,
                    "bet_odds": bet_odds,
                    "bet_prob": bet_prob,
                    "no_bet_reason": no_bet_reason,
                    "max_ev_pct": max_ev_pct,
                    "winner": None
                })
            cards_map[card_key]["fights"] = existing_fights

    # 2. Récupération des résultats passés depuis l'API officielle
    past_espn_cards = fetch_past_completed_events()
    today_str = time.strftime("%Y-%m-%d")

    for p_card in past_espn_cards:
        p_name = p_card["event_name"]
        p_date = p_card["event_date"]
        p_key = f"{p_date} | {p_name}"

        if p_key not in cards_map:
            cards_map[p_key] = {
                "event_title": p_name,
                "event_date": p_date,
                "is_completed": p_card["is_completed"],
                "fights": []
            }

        cards_map[p_key]["is_completed"] = p_card["is_completed"]
        c_fights = cards_map[p_key].get("fights", [])

        for p_fight in p_card["fights"]:
            pf1 = p_fight["f1"]
            pf2 = p_fight["f2"]
            pwinner = p_fight["winner"]

            f_found = False
            for cf in c_fights:
                m1_dir = fuzzy_match_fighter_name(pf1, [cf["f1"]], threshold=0.70)
                m2_dir = fuzzy_match_fighter_name(pf2, [cf["f2"]], threshold=0.70)
                m1_swp = fuzzy_match_fighter_name(pf1, [cf["f2"]], threshold=0.70)
                m2_swp = fuzzy_match_fighter_name(pf2, [cf["f1"]], threshold=0.70)

                if (m1_dir and m2_dir) or (m1_swp and m2_swp):
                    f_found = True
                    if pwinner:
                        cf["winner"] = pwinner
                    break

            if not f_found and pwinner:
                c_fights.append({
                    "fight_index": p_fight["fight_index"],
                    "fight_label": p_fight["fight_label"],
                    "f1": pf1,
                    "f2": pf2,
                    "has_full_data": False,
                    "has_valid_odds": False,
                    "pct_a": None,
                    "pct_b": None,
                    "odds_a": None,
                    "odds_b": None,
                    "bkm_name": None,
                    "ev_a": None,
                    "ev_b": None,
                    "is_value_bet": False,
                    "bet_fighter": None,
                    "bet_odds": None,
                    "bet_prob": None,
                    "no_bet_reason": "NO_BET_MISSING_DATA",
                    "max_ev_pct": None,
                    "winner": pwinner
                })
        cards_map[p_key]["fights"] = c_fights

    # 3. Purge stricte des doublons sur TOUTES les cartes
    for c_k in list(cards_map.keys()):
        raw_f = cards_map[c_k].get("fights", [])
        cards_map[c_k]["fights"] = deduplicate_card_fights(raw_f)

    # 4. Calcul du Bilan Financier et Précision (Point-In-Time Strict sans Data Leakage)
    total_staked = 0.0
    total_profit = 0.0
    value_bets_count = 0
    value_bets_won = 0
    total_correct_predictions = 0
    total_valid_fights = 0

    raw_df_dt = raw_df.copy()
    if "event_date_dt" not in raw_df_dt.columns:
        raw_df_dt["event_date_dt"] = pd.to_datetime(raw_df_dt["event_date"])

    for c_key, c_data in cards_map.items():
        c_date_str = c_data.get("event_date", "")
        all_fights = c_data.get("fights", [])
        winners_count = sum(1 for f in all_fights if f.get("winner"))

        if c_date_str < today_str and winners_count > 0:
            c_data["is_completed"] = True

        is_completed = c_data.get("is_completed", False)

        # Si carte passée terminée, recalcul des états dynamiques à T-1 (Point-in-time strict)
        past_raw_df = None
        p_elo, p_hist, p_ws, p_ls, p_rank = None, None, None, None, None
        if is_completed and c_date_str:
            c_dt = pd.to_datetime(c_date_str)
            past_raw_df = raw_df_dt[raw_df_dt["event_date_dt"] < c_dt]
            p_elo, p_hist, p_ws, p_ls, p_rank = compute_fighter_dynamic_states_v3(past_raw_df)

        for fight in all_fights:
            winner = fight.get("winner")
            f1_name = fight.get("f1", "")
            f2_name = fight.get("f2", "")

            is_f1_win = bool(winner and fuzzy_match_fighter_name(winner, [f1_name], threshold=0.70))
            is_f2_win = bool(winner and fuzzy_match_fighter_name(winner, [f2_name], threshold=0.70))

            is_void_or_cancelled = (
                not winner or
                str(winner).upper().strip() in ["N/A", "NONE", "DRAW/NC", "NC", "CANCELLED", "VOID", "DRAW"] or
                (not is_f1_win and not is_f2_win)
            )

            # Recalcul Point-in-time des pronostics et Value Bets pour les cartes passées
            if is_completed and past_raw_df is not None:
                h_oa, h_ob = get_historical_closing_odds(f1_name, f2_name)
                odds_a = h_oa or fight.get("odds_a")
                odds_b = h_ob or fight.get("odds_b")
                if odds_a and odds_b and odds_a > 1.0 and odds_b > 1.0:
                    fight["odds_a"] = odds_a
                    fight["odds_b"] = odds_b
                    fight["has_valid_odds"] = True

                n1 = resolve_fighter_name(f1_name, all_fighters)
                n2 = resolve_fighter_name(f2_name, all_fighters)

                p1 = get_latest_fighter_profile_v3(n1, past_raw_df, p_elo, p_hist, p_ws, p_ls, p_rank) if n1 else None
                p2 = get_latest_fighter_profile_v3(n2, past_raw_df, p_elo, p_hist, p_ws, p_ls, p_rank) if n2 else None

                f1_fights = p1.get("ufc_fights", 0) if p1 else 0
                f2_fights = p2.get("ufc_fights", 0) if p2 else 0
                has_full = bool(p1 is not None and p2 is not None and f1_fights > 0 and f2_fights > 0)

                if not has_full:
                    fight["has_full_data"] = False
                    fight["pct_a"] = None
                    fight["pct_b"] = None
                    fight["ev_a"] = None
                    fight["ev_b"] = None
                    fight["is_value_bet"] = False
                    fight["bet_fighter"] = None
                    fight["bet_odds"] = None
                    fight["bet_prob"] = None
                    fight["no_bet_reason"] = "NO_BET_MISSING_DATA"
                    fight["max_ev_pct"] = None
                else:
                    fight["has_full_data"] = True
                    delta_dict = {}
                    for stat in STAT_COLS_V1:
                        delta_key = f"delta_{stat}"
                        val_a, val_b = p1[stat], p2[stat]
                        delta_dict[delta_key] = (val_a - val_b) if (pd.notna(val_a) and pd.notna(val_b)) else medians.get(delta_key, 0.0)

                    delta_dict["delta_elo"] = p1["elo"] - p2["elo"]
                    delta_dict["delta_win_streak"] = p1["win_streak"] - p2["win_streak"]
                    delta_dict["delta_loss_streak"] = p1["loss_streak"] - p2["loss_streak"]
                    delta_dict["delta_win_rate_last_5"] = p1["win_rate_5"] - p2["win_rate_5"]
                    delta_dict["delta_ufc_win_rate"] = p1["ufc_win_rate"] - p2["ufc_win_rate"]
                    delta_dict["delta_ufc_fights"] = p1["ufc_fights"] - p2["ufc_fights"]
                    delta_dict["delta_rank"] = p2["rank"] - p1["rank"]
                    delta_dict["is_ranked_f1"] = p1["is_ranked"]
                    delta_dict["is_ranked_f2"] = p2["is_ranked"]
                    delta_dict["delta_win_rate_3y"] = p1["wr_3y"] - p2["wr_3y"]
                    delta_dict["delta_SlpM_3y"] = (p1["slpm_3y"] - p2["slpm_3y"]) if (pd.notna(p1["slpm_3y"]) and pd.notna(p2["slpm_3y"])) else medians.get("delta_SlpM_3y", 0.0)
                    delta_dict["delta_SApM_3y"] = (p1["sapm_3y"] - p2["sapm_3y"]) if (pd.notna(p1["sapm_3y"]) and pd.notna(p2["sapm_3y"])) else medians.get("delta_SApM_3y", 0.0)
                    delta_dict["delta_TD_Def_3y"] = (p1["td_def_3y"] - p2["td_def_3y"]) if (pd.notna(p1["td_def_3y"]) and pd.notna(p2["td_def_3y"])) else medians.get("delta_TD_Def_3y", 0.0)

                    X_input = pd.DataFrame([delta_dict])[FEATURE_COLS_V3]
                    probs = model.predict_proba(X_input)[0]
                    prob_b, prob_a = float(probs[0]), float(probs[1])

                    fight["pct_a"] = prob_a * 100.0
                    fight["pct_b"] = prob_b * 100.0

                    h_oa, h_ob = get_historical_closing_odds(f1_name, f2_name)
                    odds_a = h_oa or fight.get("odds_a")
                    odds_b = h_ob or fight.get("odds_b")

                    if odds_a and odds_b and odds_a > 1.0 and odds_b > 1.0:
                        fight["odds_a"] = odds_a
                        fight["odds_b"] = odds_b
                        fight["has_valid_odds"] = True
                        ev_a = (prob_a * odds_a) - 1.0
                        ev_b = (prob_b * odds_b) - 1.0
                        fight["ev_a"] = ev_a
                        fight["ev_b"] = ev_b
                        best_ev = max(ev_a, ev_b)
                        fight["max_ev_pct"] = best_ev * 100.0

                        if best_ev > 0.20:
                            fight["is_value_bet"] = True
                            fight["bet_fighter"] = f1_name if ev_a >= ev_b else f2_name
                            fight["bet_odds"] = odds_a if ev_a >= ev_b else odds_b
                            fight["bet_prob"] = prob_a if ev_a >= ev_b else prob_b
                        else:
                            fight["is_value_bet"] = False
                            fight["no_bet_reason"] = "NO_BET_LOW_EV"
                    else:
                        fight["is_value_bet"] = False
                        fight["no_bet_reason"] = "NO_BET_NO_ODDS"

            # Évaluation financière et statistiques de précision
            if is_void_or_cancelled:
                fight["result_status"] = "VOID"
                fight["net_gain"] = 0.0
            else:
                pct_a = fight.get("pct_a")
                pct_b = fight.get("pct_b")
                has_full_data = fight.get("has_full_data", False)
                if has_full_data and pct_a is not None and pct_b is not None:
                    total_valid_fights += 1
                    model_favors_f1 = (pct_a >= pct_b)
                    if (model_favors_f1 and is_f1_win) or (not model_favors_f1 and is_f2_win):
                        total_correct_predictions += 1

                if fight.get("is_value_bet"):
                    bet_f = fight.get("bet_fighter")
                    b_odds = fight.get("bet_odds") or 1.0

                    total_staked += 10.0
                    value_bets_count += 1

                    is_win = bool(bet_f and fuzzy_match_fighter_name(winner, [bet_f], threshold=0.75))
                    if is_win:
                        value_bets_won += 1
                        gain_net = 10.0 * (b_odds - 1.0)
                        total_profit += gain_net
                        fight["result_status"] = "WIN"
                        fight["net_gain"] = gain_net
                    else:
                        total_profit -= 10.0
                        fight["result_status"] = "LOSS"
                        fight["net_gain"] = -10.0

    roi_pct = (total_profit / total_staked * 100.0) if total_staked > 0 else 0.0
    win_rate_pct = (value_bets_won / value_bets_count * 100.0) if value_bets_count > 0 else 0.0
    overall_accuracy_pct = (total_correct_predictions / total_valid_fights * 100.0) if total_valid_fights > 0 else 0.0

    summary = {
        "total_profit": total_profit,
        "total_staked": total_staked,
        "roi_pct": roi_pct,
        "win_rate_pct": win_rate_pct,
        "value_bets_count": value_bets_count,
        "value_bets_won": value_bets_won,
        "total_correct_predictions": total_correct_predictions,
        "total_valid_fights": total_valid_fights,
        "overall_accuracy_pct": overall_accuracy_pct
    }

    tracker_data["cards"] = cards_map
    tracker_data["summary"] = summary
    save_historical_tracker(tracker_data)

    upcoming_cards = collections.OrderedDict()
    past_cards = collections.OrderedDict()

    sorted_card_keys = sorted(cards_map.keys())

    for k in sorted_card_keys:
        c_info = cards_map[k]
        c_date = c_info.get("event_date", "")
        is_comp = c_info.get("is_completed", False)

        if is_comp or c_date < today_str:
            past_cards[k] = c_info
        else:
            upcoming_cards[k] = c_info

    past_cards_reversed = collections.OrderedDict(reversed(list(past_cards.items())))

    return deduplicate_upcoming_cards(upcoming_cards), past_cards_reversed, summary
