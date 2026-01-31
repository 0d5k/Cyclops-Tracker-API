import os
import threading
import time
import random
import string
import requests
from collections import deque
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

TITLE_ID = "63FDD"
API_BASE = f"https://{TITLE_ID}.playfabapi.com/Client"

PUBLIC_HOST = os.getenv("PUBLIC_HOST", "")
PORT = int(os.getenv("API_PORT", "8080"))

LOBBY_CHECK_TIME = 2.8
REGION_SWITCH_DELAY = 1.5
HIT_DELAY = 4.0

TARGETS = {
    "LBAAK.": "Stick",
    "LBAAD.": "Admin Badge",
    "LBAGS.": "Illustrator Badge",
    "LMAPY.": "Forest Guide Stick",
    "LBANI.": "Another Axiom Badge"
}

COMMON_ROOMS = [
    "JMANCURLY","ELLIOT","1","MOD","67","TTT","TTTPIG","TYLERVR","MONKE","GOUP",
    "CHILL","HIDE","RUN","TREE","JUMP","CLIMB","FAST","CHASE","QUEEN","SPIDER",
    "SHADOW","TIPTOE","NINJA","SNEAK","HELP","SCREAM","LOL","YOLO","OOPS","BANJO",
    "CHIPPD","PBBC","PBBV","ECHO","MVP","BOOST","SLIDE","CRAZY","HOP","BOUNCE",
    "PEEPEE","AUDIO","BASS","DRUM","SNARE","JUMPY","GRAB","PUNCH","CLAW","TROLL",
    "OMG","XD","LUL","SREN17","SREN18","SECRET","HUNT","MORSE","LOST","MIRROR",
    "FUN123","TREE69","2","CLOUDSCOMP","GULLIBLE","MODS","ELLIOT1","VMT","JUANGTAG",
    "JMAN","VMT1","VEN1","JUAN","TUXEDO","K9","ALECVR","RED","FREDDYBOY","ITZTAPU",
    "MBEACHY","VIKINGVR","SCUBA","ZBR","FAADUU","YOTTABITE","BXT","SNICKS",
    "MBEACHYVR","CRATORVR","ICEDVR","LYNXXYY","LTMERCH","POLAR","EDDIEGT",
    "WATERMAN","LUCIO","POLSKA","POLSKA1","POLSKA3","FOGGY","EPIC","MMM",
    "MINIGAMES","B8","METADATA","METADATA2","GORILLATAG","MONKEY","MONKE","AURA","GTAG"
]

session_tickets = []
checked_rooms = set()

# THIS is what the mod reads
active_rooms = deque(maxlen=25)

app = FastAPI(docs_url=None, redoc_url=None)

def pick_room_code():
    room = random.choice(COMMON_ROOMS) if random.random() < 0.85 else \
        ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    if room in checked_rooms:
        return pick_room_code()
    checked_rooms.add(room)
    if len(checked_rooms) > 500:
        checked_rooms.clear()
    return room

def scan_room(room):
    regions = ["US", "EU", "USW"]
    random.shuffle(regions)

    for region in regions:
        lobby = f"{room}{region}"
        try:
            r = requests.post(
                f"{API_BASE}/GetSharedGroupData",
                headers={"X-Authorization": random.choice(session_tickets)},
                json={"SharedGroupId": lobby},
                timeout=8
            )
            data = r.json()
            if data.get("code") != 200:
                continue

            players = data.get("data", {}).get("Data", {})
            if not players:
                continue

            cosmetics = set()
            for pdata in players.values():
                blob = pdata.get("Value", "")
                for cid, name in TARGETS.items():
                    if cid in blob:
                        cosmetics.add(name)

            active_rooms.append({
                "code": room,
                "region": region,
                "map": "Forest",
                "gamemode": "Infection",
                "player_count": str(len(players)),
                "position_on_leaderboard": "0",
                "cosmetics": [{"name": c} for c in cosmetics]
            })

            time.sleep(HIT_DELAY)
            return

        except:
            pass

        time.sleep(REGION_SWITCH_DELAY)

def scanner_loop():
    while True:
        if not session_tickets:
            time.sleep(2)
            continue
        scan_room(pick_room_code())
        time.sleep(LOBBY_CHECK_TIME)

@app.get("/api/getcodes")
def getcodes():
    return list(active_rooms)

@app.post("/api/add_ticket")
def add_ticket(ticket: str):
    session_tickets.append(ticket)
    return {"ok": True}

threading.Thread(target=scanner_loop, daemon=True).start()
