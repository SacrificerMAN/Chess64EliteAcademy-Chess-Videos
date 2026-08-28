#!/usr/bin/env python3
"""Apply local-PGN player photo/flag fix to chess_video_agent_v2.py at Docker build."""
from pathlib import Path
import re

TARGET = Path("chess_video_agent_v2.py")
if not TARGET.exists():
    print("agent not found, skip")
    raise SystemExit(0)

text = TARGET.read_text(encoding="utf-8")

# --- 1) KNOWN_USERNAMES + _slug_candidates ---
NEW_SLUG = r'''KNOWN_USERNAMES = {
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

pattern_slug = re.compile(
    r"KNOWN_USERNAMES\s*=\s*\{.*?\n\ndef _slug_candidates\(name: str\):.*?\n    return out\n\n",
    re.DOTALL,
)
text2, n1 = pattern_slug.subn(NEW_SLUG, text, count=1)

# --- 2) resolve_player_assets with name verification ---
NEW_RESOLVE = r'''def resolve_player_assets(display_name: str) -> tuple:
    """
    Returns (photo_path, flag_path) using Chess.com avatar + country flag.
    Caches under SCRIPT_DIR/players and SCRIPT_DIR/flags.
    Verifies profile name matches requested display name so random users
    (e.g. WesleySo ≠ Wesley So) never steal the photo.
    """
    import urllib.request
    import re as _re

    players_dir = SCRIPT_DIR / "players"
    flags_dir = SCRIPT_DIR / "flags"
    players_dir.mkdir(exist_ok=True)
    flags_dir.mkdir(exist_ok=True)

    def _tokens(s: str):
        return set(_re.findall(r"[a-z]{3,}", (s or "").lower()))

    want = _tokens(display_name)
    want = {t for t in want if t not in ("the", "and", "von", "van", "de", "la")}

    profile = None
    used_user = None
    for cand in _slug_candidates(display_name):
        prof = fetch_chesscom_profile(cand)
        if not prof or not prof.get("avatar"):
            continue
        # Prefer known mapped usernames always
        if cand in KNOWN_USERNAMES.values():
            profile, used_user = prof, cand
            break
        # Otherwise require name overlap (avoid WesleySo → random PH user)
        got = _tokens(prof.get("name") or "") | _tokens(prof.get("username") or "")
        if want and got and (want & got):
            profile, used_user = prof, cand
            break
        if not want:
            profile, used_user = prof, cand
            break

    photo_path = None
    flag_path = None

    if profile:
        avatar_url = profile.get("avatar")
        if avatar_url:
            safe = _re.sub(r"[^a-zA-Z0-9_-]", "_", (used_user or display_name).lower())[:40]
            dest = players_dir / f"{safe}.jpg"
            if not dest.exists() or dest.stat().st_size < 500:
                try:
                    req = urllib.request.Request(avatar_url, headers={"User-Agent": "ChessVideoAgent/1.0"})
                    with urllib.request.urlopen(req, timeout=10) as r:
                        dest.write_bytes(r.read())
                except Exception as e:
                    print(f"  avatar download failed for {display_name}: {e}")
            if dest.exists() and dest.stat().st_size > 500:
                photo_path = str(dest)

        country_url = profile.get("country") or ""
        code = country_url.rstrip("/").split("/")[-1].lower() if country_url else ""
        if code and len(code) == 2:
            fdest = flags_dir / f"{code}.png"
            if not fdest.exists() or fdest.stat().st_size < 50:
                try:
                    flag_url = f"https://flagcdn.com/w80/{code}.png"
                    req = urllib.request.Request(flag_url, headers={"User-Agent": "ChessVideoAgent/1.0"})
                    with urllib.request.urlopen(req, timeout=8) as r:
                        fdest.write_bytes(r.read())
                except Exception as e:
                    print(f"  flag download failed {code}: {e}")
            if fdest.exists() and fdest.stat().st_size > 50:
                flag_path = str(fdest)

    return photo_path, flag_path


'''

pattern_res = re.compile(
    r"def resolve_player_assets\(display_name: str\) -> tuple:.*?\n    return photo_path, flag_path\n\n\n",
    re.DOTALL,
)
text3, n2 = pattern_res.subn(NEW_RESOLVE, text2 if n1 else text, count=1)

if n1 == 0 and "so, wesley" not in text and "caruana, fabiano" not in text:
    print("WARN: slug patch not applied")
if n2 == 0:
    if "Prefer known mapped usernames" in text:
        print("resolve already has name verify")
    else:
        print("WARN: resolve patch not applied, n2=", n2)

TARGET.write_text(text3 if n2 else (text2 if n1 else text), encoding="utf-8")
print(f"applied: slug={n1} resolve={n2}")
