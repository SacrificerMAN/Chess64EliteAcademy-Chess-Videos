"""List recent decisive Chess.com games for picker UI."""
from __future__ import annotations
import json, re, urllib.request
from typing import Any, Dict, List

HINTS = ("tournament","championship","candidates","olympiad","fide","grand prix",
         "grand swiss","world cup","masters","gct","grand chess tour","tata steel",
         "norway chess","sinquefield","superbet","classical")

def _tag(pgn, tag):
    m = re.search(rf'\[{tag}\s+"([^"]*)"\]', pgn or "")
    return m.group(1) if m else ""

def _json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Chess64/2.1"})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read().decode())

def _otb(event, tc=""):
    e = (event or "").lower()
    if not e or "live chess" in e:
        return False
    if any(h in e for h in HINTS):
        return True
    return e not in ("live chess","chess.com","online") and len(e) > 10

def list_recent_decisive(player_query, source="chesscom", limit=10, prefer_otb=True):
    from fix_resolve import KNOWN, _candidates
    uname = None
    for c in _candidates(player_query):
        if c in KNOWN.values():
            uname = c
            break
    if not uname:
        cs = _candidates(player_query)
        uname = cs[0] if cs else player_query.replace(" ", "")

    arch = _json(f"https://api.chess.com/pub/player/{uname}/games/archives")
    months = list(reversed(arch.get("archives") or []))[:6]
    raw = []
    for u in months:
        try:
            raw.extend((_json(u) or {}).get("games") or [])
        except Exception:
            pass
    raw.sort(key=lambda g: g.get("end_time", 0), reverse=True)

    out = []
    for g in raw:
        pgn = g.get("pgn") or ""
        if not pgn.strip():
            continue
        result = _tag(pgn, "Result")
        if result not in ("1-0", "0-1"):
            continue
        event = _tag(pgn, "Event")
        tc = g.get("time_class") or ""
        is_otb = _otb(event, tc)
        if source in ("tournament", "fide", "otb") and not is_otb:
            continue
        out.append({
            "white": _tag(pgn, "White") or (g.get("white") or {}).get("username", "?"),
            "black": _tag(pgn, "Black") or (g.get("black") or {}).get("username", "?"),
            "result": result,
            "event": event or "Live Chess",
            "time_class": tc,
            "url": g.get("url") or "",
            "end_time": g.get("end_time") or 0,
            "is_otb": is_otb,
            "pgn": pgn,
        })
        if len(out) >= max(limit * 3, 30):
            break
    if prefer_otb:
        out.sort(key=lambda x: (0 if x["is_otb"] else 1, -x["end_time"]))
    else:
        out.sort(key=lambda x: -x["end_time"])
    return out[:limit]
