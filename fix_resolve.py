"""Correct Chess.com photo/flag resolver for local PGN names (Last, First)."""
from __future__ import annotations
import json
import re
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent

KNOWN = {
    "magnus carlsen": "MagnusCarlsen",
    "hikaru nakamura": "Hikaru",
    "hikaru": "Hikaru",
    "fabiano caruana": "FabianoCaruana",
    "caruana, fabiano": "FabianoCaruana",
    "caruana fabiano": "FabianoCaruana",
    "ding liren": "DingLiren",
    "ian nepomniachtchi": "lachesisQ",
    "alireza firouzja": "Firouzja2003",
    "wesley so": "GMWSO",
    "so, wesley": "GMWSO",
    "so wesley": "GMWSO",
    "vincent keymer": "VincentKeymer",
    "keymer, vincent": "VincentKeymer",
    "keymer vincent": "VincentKeymer",
    "praggnanandhaa": "rpragchess",
    "praggnanandhaa r": "rpragchess",
    "r praggnanandhaa": "rpragchess",
    "pragg": "rpragchess",
    "gukesh d": "GukeshDommaraju",
    "gukesh": "GukeshDommaraju",
    "anish giri": "AnishGiri",
    "levon aronian": "LevAronian",
}

def _candidates(name: str):
    n = (name or "").strip()
    if not n:
        return []
    out, seen = [], set()
    def add(x):
        if x and x.lower() not in seen:
            seen.add(x.lower()); out.append(x)
    key = n.lower()
    if key in KNOWN:
        add(KNOWN[key])
    if "," in n:
        a, b = [p.strip() for p in n.split(",", 1)]
        fl = f"{b} {a}".strip()
        if fl.lower() in KNOWN:
            add(KNOWN[fl.lower()])
        add("".join(fl.split()))
    parts = re.sub(r"[^A-Za-z0-9 ]", "", n).split()
    if parts:
        add("".join(parts))
        if len(parts) >= 2:
            add(parts[-1] + parts[0])
    return out

def _fetch(username: str) -> Optional[dict]:
    url = f"https://api.chess.com/pub/player/{username}"
    req = urllib.request.Request(url, headers={"User-Agent": "Chess64/2.1"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None

def resolve_player_assets(display_name: str) -> Tuple[Optional[str], Optional[str]]:
    players = SCRIPT_DIR / "players"
    flags = SCRIPT_DIR / "flags"
    players.mkdir(exist_ok=True)
    flags.mkdir(exist_ok=True)

    want = set(re.findall(r"[a-z]{3,}", (display_name or "").lower()))
    profile, used = None, None
    for cand in _candidates(display_name):
        prof = _fetch(cand)
        if not prof or not prof.get("avatar"):
            continue
        if cand in KNOWN.values():
            profile, used = prof, cand
            break
        got = set(re.findall(r"[a-z]{3,}", (prof.get("name") or "").lower()))
        if want and got and (want & got):
            profile, used = prof, cand
            break
    if not profile:
        return None, None

    photo = flag = None
    avatar = profile.get("avatar")
    if avatar:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", (used or display_name).lower())[:40]
        dest = players / f"{safe}.jpg"
        try:
            req = urllib.request.Request(avatar, headers={"User-Agent": "Chess64/2.1"})
            with urllib.request.urlopen(req, timeout=10) as r:
                dest.write_bytes(r.read())
            if dest.stat().st_size > 500:
                photo = str(dest)
        except Exception as e:
            print(f"avatar fail {display_name}: {e}")

    country = (profile.get("country") or "").rstrip("/").split("/")[-1].lower()
    if len(country) == 2:
        fdest = flags / f"{country}.png"
        if not fdest.exists() or fdest.stat().st_size < 50:
            try:
                req = urllib.request.Request(
                    f"https://flagcdn.com/w80/{country}.png",
                    headers={"User-Agent": "Chess64/2.1"},
                )
                with urllib.request.urlopen(req, timeout=8) as r:
                    fdest.write_bytes(r.read())
            except Exception:
                pass
        if fdest.exists() and fdest.stat().st_size > 50:
            flag = str(fdest)
    return photo, flag
