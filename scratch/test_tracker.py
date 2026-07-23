import os
import sys
import json
import time
import requests

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OFFICIAL_UFC_API_URL = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

url = f"{OFFICIAL_UFC_API_URL}?dates=20260101-{time.strftime('%Y%m%d')}"
print(f"Querying 2026 events: {url}")

res = requests.get(url, headers=headers, timeout=10)
if res.status_code == 200:
    data = res.json()
    events_data = data.get("events", [])
    print(f"Total 2026 events found: {len(events_data)}")
    for ev in events_data[-3:]:
        event_name = ev.get("name", "")
        event_date = ev.get("date", "")[:10]
        status_state = ev.get("status", {}).get("type", {}).get("state", "")
        print(f"\nEvent: {event_date} | {event_name} | Status: {status_state}")
        competitions = ev.get("competitions", [])
        for comp in list(reversed(competitions))[:3]:
            comps = comp.get("competitors", [])
            if len(comps) >= 2:
                c1 = comps[0]
                c2 = comps[1]
                f1_name = c1.get("athlete", {}).get("displayName", "")
                f2_name = c2.get("athlete", {}).get("displayName", "")
                w1 = c1.get("winner", False)
                w2 = c2.get("winner", False)
                winner_name = f1_name if w1 else (f2_name if w2 else "None/Draw")
                print(f"  Fight: {f1_name} vs {f2_name} ==> Winner: {winner_name}")
