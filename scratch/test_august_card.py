import os
import sys
import json
import requests
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.odds_api import get_official_ufc_cards, match_odds_to_fight
from src.utils import normalize_fighter_name, fuzzy_match_fighter_name

load_dotenv()

api_key = os.getenv("ODDS_API_KEY", "").strip()
print("API Key present:", bool(api_key))

params = {
    "apiKey": api_key,
    "regions": "eu,us",
    "markets": "h2h",
    "oddsFormat": "decimal"
}

url = "https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds/"
res = requests.get(url, params=params, timeout=10)

if res.status_code == 200:
    raw_odds_events = res.json()
    print(f"Raw events from The Odds API: {len(raw_odds_events)}")
    for idx, ev in enumerate(raw_odds_events, 1):
        h = ev.get("home_team")
        a = ev.get("away_team")
        dt = ev.get("commence_time")
        bkms = ev.get("bookmakers", [])
        print(f"  [{idx:02d}] {dt[:10]} | {h} vs {a} | Bookmakers: {len(bkms)}")

    official_cards = get_official_ufc_cards()
    print(f"\nOfficial UFC cards from ESPN: {len(official_cards)}")
    for card in official_cards:
        print(f"\nCARD: {card['event_date']} | {card['event_name']} ({len(card['fights'])} fights)")
        for fight in card['fights']:
            f1 = fight['f1']
            f2 = fight['f2']
            bkm_list = match_odds_to_fight(f1, f2, raw_odds_events)
            print(f"  Fight: {f1} vs {f2} ==> Bookmakers matched: {len(bkm_list)}")
else:
    print(f"Error fetching The Odds API: {res.status_code}")
