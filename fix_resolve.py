"""Chess.com photo/flag resolver — local PGN names (Last, First) + known GMs."""
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
    "jan-krzysztof duda": "Polish_fighter3000",
    "jan krzysztof duda": "Polish_fighter3000",
    "duda, jan-krzysztof": "Polish_fighter3000",
    "duda, jan krzysztof": "Polish_fighter3000",
    "duda": "Polish_fighter3000",
    "arjun erigaisi": "GHANDEEVAM2003",
    "erigaisi arjun": "GHANDEEVAM2003",
    "erigaisi, arjun": "GHANDEEVAM2003",
    "erigaisi": "GHANDEEVAM2003",
    "ghandeevam2003": "GHANDEEVAM2003",
    "nodirbek abdusattorov": "ChessWarrior7197",
    "richard rapport": "rapport67",
    "shakhriyar mamedyarov": "LordShakh",
    "maxime vachier-lagrave": "LyonCat",
    "maxime vachier lagrave": "LyonCat",
    "viswanathan anand": "Viswanathananand",
    "sergey karjakin": "SergeyKarjakin",
    "vladimir kramnik": "VladimirKramnik",
    "parham maghsoodloo": "ParhamMaghsoodloo",
    "maghsoodloo, parham": "ParhamMaghsoodloo",
    "maghsoodloo parham": "ParhamMaghsoodloo",
    "maghsoodloo, parham": "ParhamMaghsoodloo",
    "maghsoodloo parham": "ParhamMaghsoodloo",
    "parham maghsoodloo": "ParhamMaghsoodloo",
    "maghsoodloo": "ParhamMaghsoodloo",
    "maghsoodloo": "ParhamMaghsoodloo",
    "anthony atanasov": "aa175",
    "atanasov, anthony": "aa175",
    "atanasov anthony": "aa175",
    "atanasov": "aa175",
}


def _candidates(name: str):
    n = (name or "").strip()
    if not n:
        return []
    out, seen = [], set()

    def add(x):
        if x and x.lower() not in seen:
            seen.add(x.lower())
            out.append(x)

    key = n.lower()
    if key in KNOWN:
        add(KNOWN[key])
    for part in re.findall(r"[A-Za-z]{3,}", n):
        if part.lower() in KNOWN:
            add(KNOWN[part.lower()])
    for t in ("GM ", "IM ", "FM ", "WGM ", "WIM ", "CM ", "WCM "):
        if n.upper().startswith(t.strip() + " ") or n.startswith(t):
            n2 = n[len(t) :].strip()
            if n2.lower() in KNOWN:
                add(KNOWN[n2.lower()])
            n = n2
            break
    if "," in n:
        a, b = [p.strip() for p in n.split(",", 1)]
        fl = f"{b} {a}".strip()
        if fl.lower() in KNOWN:
            add(KNOWN[fl.lower()])
        add("".join(fl.split()))
        fl2 = fl.replace("-", " ")
        if fl2.lower() in KNOWN:
            add(KNOWN[fl2.lower()])
    parts = re.sub(r"[^A-Za-z0-9 \-]", "", n).replace("-", " ").split()
    if parts:
        add("".join(parts))
        if len(parts) >= 2:
            add(parts[-1] + parts[0])
            add(parts[0] + parts[-1])
            joined = " ".join(parts).lower()
            if joined in KNOWN:
                add(KNOWN[joined])
    return out


def _fetch(username: str):
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
    want -= {"the", "and", "von", "van"}
    profile, used = None, None
    known_vals = {v.lower() for v in KNOWN.values()}
    for cand in _candidates(display_name):
        prof = _fetch(cand)
        if not prof:
            continue
        if cand.lower() in known_vals:
            profile, used = prof, cand
            break
        if not prof.get("avatar"):
            continue
        got = set(re.findall(r"[a-z]{3,}", (prof.get("name") or "").lower()))
        if want and got and (want & got):
            profile, used = prof, cand
            break
    if not profile:
        print(f"  no photo match for: {display_name!r} cands={_candidates(display_name)}")
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
                print(f"  avatar ok: {display_name} → {used}")
        except Exception as e:
            print(f"  avatar fail {display_name}: {e}")

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
