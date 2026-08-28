#!/usr/bin/env python3
"""Apply local-PGN player photo/flag fix to chess_video_agent_v2.py at Docker build."""
from pathlib import Path
import re

TARGET = Path("chess_video_agent_v2.py")
if not TARGET.exists():
    print("agent not found, skip")
    raise SystemExit(0)

text = TARGET.read_text(encoding="utf-8")

NEW = r'''KNOWN_USERNAMES = {
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
    "levon aronian": "LevAronian",
    "anish giri": "AnishGiri",
    "maxime vachier-lagrave": "LyonCat",
    "maxime vachier lagrave": "LyonCat",
    "viswanathan anand": "Viswanathananand",
    "gukesh d": "GukeshDommaraju",
    "gukesh": "GukeshDommaraju",
    "praggnanandhaa": "rpragchess",
    "praggnanandhaa r": "rpragchess",
    "r praggnanandhaa": "rpragchess",
    "pragg": "rpragchess",
    "nodirbek abdusattorov": "ChessWarrior7197",
    "richard rapport": "rapport67",
    "shakhriyar mamedyarov": "LordShakh",
    "sergey karjakin": "SergeyKarjakin",
    "vladimir kramnik": "VladimirKramnik",
    "garry kasparov": "GarryKasparov",
    "bobby fischer": "BobbyFischer",
}

def _slug_candidates(name: str):
    """Build Chess.com username candidates from PGN-style or display names.
    Handles 'Last, First', titles, and known aliases so local PGN also gets photos/flags.
    """
    n = (name or "").strip()
    if not n:
        return []
    cands = []
    key = n.lower().strip()
    if key in KNOWN_USERNAMES:
        cands.append(KNOWN_USERNAMES[key])
    for t in ("GM ", "IM ", "FM ", "WGM ", "WIM ", "CM ", "WCM "):
        if n.upper().startswith(t.strip() + " ") or n.startswith(t):
            n = n[len(t):].strip()
            key = n.lower()
            if key in KNOWN_USERNAMES:
                cands.append(KNOWN_USERNAMES[key])
    if "," in n:
        parts_c = [p.strip() for p in n.split(",", 1)]
        if len(parts_c) == 2 and parts_c[0] and parts_c[1]:
            first_last = f"{parts_c[1]} {parts_c[0]}".strip()
            fl_key = first_last.lower()
            if fl_key in KNOWN_USERNAMES:
                cands.append(KNOWN_USERNAMES[fl_key])
            fl_joined = "".join(first_last.split())
            cands.append(fl_joined)
            cands.append(fl_joined.lower())
            cands.append("".join(parts_c[0].split()) + "".join(parts_c[1].split()))
    parts = re.sub(r"[^A-Za-z0-9 ]", "", n).split()
    if parts:
        cands.append("".join(parts))
        cands.append("".join(parts).lower())
        if len(parts) >= 2:
            cands.append(parts[-1])
            cands.append(parts[0] + parts[-1])
            cands.append(parts[-1] + parts[0])
        if len(parts) == 1 and parts[0].lower() in KNOWN_USERNAMES:
            cands.append(KNOWN_USERNAMES[parts[0].lower()])
    seen = set()
    out = []
    for c in cands:
        if c and c.lower() not in seen:
            seen.add(c.lower())
            out.append(c)
    return out


'''

pattern = re.compile(
    r"KNOWN_USERNAMES\s*=\s*\{.*?\n\ndef _slug_candidates\(name: str\):.*?\n    return out\n\n",
    re.DOTALL,
)
new_text, n = pattern.subn(NEW, text, count=1)
if n != 1:
    if "caruana, fabiano" in text and "praggnanandhaa r" in text:
        print("already has fix, ok")
        raise SystemExit(0)
    print("WARN: pattern replace count=", n)
    raise SystemExit("failed to apply player fix")
TARGET.write_text(new_text, encoding="utf-8")
print("applied player photo/flag fix for local PGN names")
