"""Chess.com photo/flag resolver — automatic for any player (no per-player hardcode needed).

Strategy:
1) Known map (fast path for odd usernames like aa175, GMWSO)
2) Generate slug candidates from "Last, First" / "First Last"
3) Score Chess.com profiles by name-token overlap
4) Scan titled GM/IM username lists for last-name hits, fetch & score
5) Accept best score above threshold → avatar + country flag
"""
from __future__ import annotations
import json
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
_CACHE_DIR = SCRIPT_DIR / ".chesscom_cache"
_CACHE_DIR.mkdir(exist_ok=True)

# Only odd usernames that NEVER match FirstLast pattern
KNOWN = {
    "magnus carlsen": "MagnusCarlsen",
    "hikaru nakamura": "Hikaru",
    "hikaru": "Hikaru",
    "wesley so": "GMWSO",
    "so, wesley": "GMWSO",
    "so wesley": "GMWSO",
    "ian nepomniachtchi": "lachesisQ",
    "alireza firouzja": "Firouzja2003",
    "jan-krzysztof duda": "Polish_fighter3000",
    "jan krzysztof duda": "Polish_fighter3000",
    "duda, jan-krzysztof": "Polish_fighter3000",
    "duda, jan krzysztof": "Polish_fighter3000",
    "duda": "Polish_fighter3000",
    "arjun erigaisi": "GHANDEEVAM2003",
    "erigaisi arjun": "GHANDEEVAM2003",
    "erigaisi, arjun": "GHANDEEVAM2003",
    "erigaisi": "GHANDEEVAM2003",
    "anthony atanasov": "aa175",
    "atanasov, anthony": "aa175",
    "atanasov anthony": "aa175",
    "nodirbek abdusattorov": "ChessWarrior7197",
    "maxime vachier-lagrave": "LyonCat",
    "maxime vachier lagrave": "LyonCat",
    "levon aronian": "LevAronian",
    "praggnanandhaa": "rpragchess",
    "praggnanandhaa r": "rpragchess",
    "r praggnanandhaa": "rpragchess",
    "pragg": "rpragchess",
    "gukesh d": "GukeshDommaraju",
    "gukesh": "GukeshDommaraju",
    "fabiano caruana": "FabianoCaruana",
    "caruana, fabiano": "FabianoCaruana",
    "caruana fabiano": "FabianoCaruana",
}

_titled_usernames: Optional[List[str]] = None


def _http_json(url: str, timeout: int = 12):
    req = urllib.request.Request(url, headers={"User-Agent": "Chess64/2.2"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _tokens(s: str) -> set:
    return {t for t in re.findall(r"[a-z]{3,}", (s or "").lower()) if t not in ("the", "and", "von", "van", "de", "la")}


def _candidates(name: str) -> List[str]:
    n = (name or "").strip()
    if not n:
        return []
    out, seen = [], set()

    def add(x):
        if not x:
            return
        xl = x.lower()
        if xl not in seen:
            seen.add(xl)
            out.append(x)

    key = re.sub(r"\s+", " ", n.lower()).strip()
    if key in KNOWN:
        add(KNOWN[key])

    for t in ("GM ", "IM ", "FM ", "WGM ", "WIM ", "CM ", "WCM "):
        if n.upper().startswith(t.strip() + " ") or n.startswith(t):
            n = n[len(t) :].strip()
            key = n.lower()
            if key in KNOWN:
                add(KNOWN[key])
            break

    if "," in n:
        a, b = [p.strip() for p in n.split(",", 1)]
        fl = f"{b} {a}".strip()
        if fl.lower() in KNOWN:
            add(KNOWN[fl.lower()])
        add("".join(ch for ch in fl if ch.isalnum()))
        add(b.replace(" ", "") + a.replace(" ", ""))
        add(a.replace(" ", "") + b.replace(" ", ""))
        if b:
            add((b[0] + a).replace(" ", ""))
    else:
        parts = re.sub(r"[^A-Za-z0-9 \-]", " ", n).replace("-", " ").split()
        if parts:
            add("".join(parts))
            if len(parts) >= 2:
                add(parts[-1] + parts[0])
                add(parts[0] + parts[-1])
                add("".join(parts[1:] + parts[:1]))
                joined = " ".join(parts).lower()
                if joined in KNOWN:
                    add(KNOWN[joined])

    parts2 = re.sub(r"[^A-Za-z0-9 \-]", " ", n).replace("-", " ").replace(",", " ").split()
    if parts2:
        longest = max(parts2, key=len)
        if len(longest) >= 5:
            add(longest)

    return out


def _fetch_profile(username: str) -> Optional[dict]:
    cache = _CACHE_DIR / f"p_{username.lower()}.json"
    if cache.exists() and cache.stat().st_size > 20:
        try:
            return json.loads(cache.read_text())
        except Exception:
            pass
    try:
        data = _http_json(f"https://api.chess.com/pub/player/{username}", timeout=8)
        try:
            cache.write_text(json.dumps(data))
        except Exception:
            pass
        return data
    except Exception:
        return None


def _score_profile(display_name: str, prof: dict) -> float:
    want = _tokens(display_name)
    if not want:
        return 0.0
    got = _tokens(prof.get("name") or "") | _tokens(prof.get("username") or "")
    if not got:
        return 0.0
    inter = want & got
    if not inter:
        uname = (prof.get("username") or "").lower()
        for t in sorted(want, key=len, reverse=True):
            if len(t) >= 5 and t[:5] in uname:
                return 0.35
        return 0.0
    return len(inter) / max(len(want), 1)


def _load_titled() -> List[str]:
    global _titled_usernames
    if _titled_usernames is not None:
        return _titled_usernames
    cache = _CACHE_DIR / "titled_gm_im.json"
    if cache.exists():
        try:
            _titled_usernames = json.loads(cache.read_text())
            if isinstance(_titled_usernames, list) and len(_titled_usernames) > 100:
                return _titled_usernames
        except Exception:
            pass
    users: List[str] = []
    for title in ("GM", "IM"):
        try:
            data = _http_json(f"https://api.chess.com/pub/titled/{title}", timeout=45)
            users.extend(data.get("players") or [])
        except Exception as e:
            print(f"  titled {title} load fail: {e}")
    seen = set()
    out = []
    for u in users:
        ul = u.lower()
        if ul not in seen:
            seen.add(ul)
            out.append(u)
    _titled_usernames = out
    try:
        cache.write_text(json.dumps(out))
    except Exception:
        pass
    print(f"  titled index: {len(out)} GM+IM usernames")
    return out


def _titled_candidates(display_name: str, limit: int = 12) -> List[str]:
    want = sorted(_tokens(display_name), key=len, reverse=True)
    if not want:
        return []
    keys = [t for t in want if len(t) >= 4][:3]
    if not keys:
        return []
    hits = []
    for u in _load_titled():
        ul = u.lower()
        for k in keys:
            if k in ul or (len(k) >= 5 and k[:5] in ul):
                hits.append(u)
                break
        if len(hits) >= limit:
            break
    return hits


def resolve_player_assets(display_name: str) -> Tuple[Optional[str], Optional[str]]:
    players = SCRIPT_DIR / "players"
    flags = SCRIPT_DIR / "flags"
    players.mkdir(exist_ok=True)
    flags.mkdir(exist_ok=True)

    name = (display_name or "").strip()
    if not name or name.lower() in ("white", "black", "?"):
        return None, None

    cands: List[str] = []
    seen = set()
    for c in _candidates(name) + _titled_candidates(name):
        cl = c.lower()
        if cl not in seen:
            seen.add(cl)
            cands.append(c)

    best_prof, best_user, best_score = None, None, 0.0
    known_vals = {v.lower() for v in KNOWN.values()}

    for cand in cands[:20]:
        prof = _fetch_profile(cand)
        if not prof:
            continue
        if cand.lower() in known_vals:
            best_prof, best_user, best_score = prof, cand, 1.0
            break
        sc = _score_profile(name, prof)
        if sc > best_score:
            best_score, best_prof, best_user = sc, prof, cand

    if not best_prof or best_score < 0.34:
        print(f"  no photo match for: {name!r} best={best_score:.2f} cands={cands[:8]}")
        return None, None

    print(f"  avatar match: {name!r} → {best_user} (score={best_score:.2f})")

    photo = flag = None
    avatar = best_prof.get("avatar")
    if avatar:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", (best_user or name).lower())[:40]
        dest = players / f"{safe}.jpg"
        try:
            if not dest.exists() or dest.stat().st_size < 500:
                req = urllib.request.Request(avatar, headers={"User-Agent": "Chess64/2.2"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    dest.write_bytes(r.read())
            if dest.exists() and dest.stat().st_size > 500:
                photo = str(dest)
        except Exception as e:
            print(f"  avatar download fail {name}: {e}")

    country = (best_prof.get("country") or "").rstrip("/").split("/")[-1].lower()
    if len(country) == 2:
        fdest = flags / f"{country}.png"
        if not fdest.exists() or fdest.stat().st_size < 50:
            try:
                req = urllib.request.Request(
                    f"https://flagcdn.com/w80/{country}.png",
                    headers={"User-Agent": "Chess64/2.2"},
                )
                with urllib.request.urlopen(req, timeout=8) as r:
                    fdest.write_bytes(r.read())
            except Exception:
                pass
        if fdest.exists() and fdest.stat().st_size > 50:
            flag = str(fdest)

    return photo, flag
