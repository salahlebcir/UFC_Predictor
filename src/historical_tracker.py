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
BASELINE_DATE = "2026-06-20"  # Baseline officielle incluant 5 cartes passées (du 20 Juin 2026 au 25 Juillet 2026)
OFFICIAL_UFC_API_URL = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"


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

    # 4. Calcul du Bilan Financier Cumulé (Baseline 19 Juillet 2026, Mise fixe 10 €)
    total_staked = 0.0
    total_profit = 0.0
    value_bets_count = 0
    value_bets_won = 0

    for c_key, c_data in cards_map.items():
        c_date = c_data.get("event_date", "")
        all_fights = c_data.get("fights", [])
        winners_count = sum(1 for f in all_fights if f.get("winner"))

        if c_date < today_str and winners_count > 0:
            c_data["is_completed"] = True

        for fight in all_fights:
            winner = fight.get("winner")
            f1_name = fight.get("f1", "")
            f2_name = fight.get("f2", "")

            # Vérification si le combat est annulé / no contest / sans vainqueur valide
            is_f1_win = bool(winner and fuzzy_match_fighter_name(winner, [f1_name], threshold=0.70))
            is_f2_win = bool(winner and fuzzy_match_fighter_name(winner, [f2_name], threshold=0.70))

            is_void_or_cancelled = (
                not winner or
                str(winner).upper().strip() in ["N/A", "NONE", "DRAW/NC", "NC", "CANCELLED", "VOID", "DRAW"] or
                (not is_f1_win and not is_f2_win)
            )

            if is_void_or_cancelled:
                fight["result_status"] = "VOID"
                fight["net_gain"] = 0.0
            elif fight.get("is_value_bet"):
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

    summary = {
        "total_profit": total_profit,
        "total_staked": total_staked,
        "roi_pct": roi_pct,
        "win_rate_pct": win_rate_pct,
        "value_bets_count": value_bets_count,
        "value_bets_won": value_bets_won
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
