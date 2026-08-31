"""Auto Chess.com photo/flag resolver + Wikipedia/initials fallback."""
from __future__ import annotations
import json, re, urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
_CACHE = SCRIPT_DIR / ".chesscom_cache"
_CACHE.mkdir(exist_ok=True)

KNOWN = {
    "magnus carlsen": "MagnusCarlsen", "hikaru nakamura": "Hikaru", "hikaru": "Hikaru",
    "wesley so": "GMWSO", "so, wesley": "GMWSO", "so wesley": "GMWSO",
    "ian nepomniachtchi": "lachesisQ", "alireza firouzja": "Firouzja2003",
    "jan-krzysztof duda": "Polish_fighter3000", "duda, jan-krzysztof": "Polish_fighter3000",
    "duda, jan krzysztof": "Polish_fighter3000", "duda": "Polish_fighter3000",
    "arjun erigaisi": "GHANDEEVAM2003", "erigaisi arjun": "GHANDEEVAM2003",
    "erigaisi, arjun": "GHANDEEVAM2003", "erigaisi": "GHANDEEVAM2003",
    "anthony atanasov": "aa175", "atanasov, anthony": "aa175", "atanasov anthony": "aa175",
    "nodirbek abdusattorov": "ChessWarrior7197", "maxime vachier-lagrave": "LyonCat",
    "levon aronian": "LevAronian", "praggnanandhaa": "rpragchess",
    "praggnanandhaa r": "rpragchess", "pragg": "rpragchess",
    "gukesh d": "GukeshDommaraju", "gukesh": "GukeshDommaraju",
    "fabiano caruana": "FabianoCaruana", "caruana, fabiano": "FabianoCaruana",
}

_titled = None

def _json(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "Chess64/2.3"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

def _tokens(s):
    return {t for t in re.findall(r"[a-z]{3,}", (s or "").lower()) if t not in ("the","and","von","van","de","la")}

def _candidates(name):
    n = (name or "").strip()
    if not n: return []
    out, seen = [], set()
    def add(x):
        if x and x.lower() not in seen:
            seen.add(x.lower()); out.append(x)
    key = re.sub(r"\s+", " ", n.lower()).strip()
    if key in KNOWN: add(KNOWN[key])
    for t in ("GM ","IM ","FM ","WGM ","WIM "):
        if n.upper().startswith(t.strip()+" ") or n.startswith(t):
            n = n[len(t):].strip()
            if n.lower() in KNOWN: add(KNOWN[n.lower()])
            break
    if "," in n:
        a,b = [p.strip() for p in n.split(",",1)]
        fl = f"{b} {a}".strip()
        if fl.lower() in KNOWN: add(KNOWN[fl.lower()])
        add("".join(ch for ch in fl if ch.isalnum()))
        add(b.replace(" ","")+a.replace(" ","")); add(a.replace(" ","")+b.replace(" ",""))
    else:
        parts = re.sub(r"[^A-Za-z0-9 \-]"," ",n).replace("-"," ").split()
        if parts:
            add("".join(parts))
            if len(parts)>=2:
                add(parts[-1]+parts[0]); add(parts[0]+parts[-1])
    parts2 = re.sub(r"[^A-Za-z0-9 \-]"," ",n).replace("-"," ").replace(","," ").split()
    if parts2:
        longest = max(parts2, key=len)
        if len(longest)>=5: add(longest)
    return out

def _fetch(username):
    cache = _CACHE / f"p_{username.lower()}.json"
    if cache.exists() and cache.stat().st_size>20:
        try: return json.loads(cache.read_text())
        except Exception: pass
    try:
        data = _json(f"https://api.chess.com/pub/player/{username}", 8)
        try: cache.write_text(json.dumps(data))
        except Exception: pass
        return data
    except Exception:
        return None

def _score(name, prof):
    want, got = _tokens(name), _tokens(prof.get("name") or "") | _tokens(prof.get("username") or "")
    if not want or not got: return 0.0
    inter = want & got
    if not inter:
        uname = (prof.get("username") or "").lower()
        for t in sorted(want, key=len, reverse=True):
            if len(t)>=5 and t[:5] in uname: return 0.35
        return 0.0
    sc = len(inter)/max(len(want),1)
    if prof.get("title"): sc = min(1.0, sc+0.15)
    if prof.get("avatar"): sc = min(1.0, sc+0.1)
    return sc

def _load_titled():
    global _titled
    if _titled is not None: return _titled
    cache = _CACHE / "titled_gm_im.json"
    if cache.exists():
        try:
            _titled = json.loads(cache.read_text())
            if len(_titled)>100: return _titled
        except Exception: pass
    users=[]
    for title in ("GM","IM"):
        try: users.extend(_json(f"https://api.chess.com/pub/titled/{title}",45).get("players") or [])
        except Exception as e: print(f"  titled {title} fail: {e}")
    seen=set(); out=[]
    for u in users:
        if u.lower() not in seen:
            seen.add(u.lower()); out.append(u)
    _titled = out
    try: cache.write_text(json.dumps(out))
    except Exception: pass
    print(f"  titled index: {len(out)}")
    return out

def _titled_cands(name, limit=12):
    keys = [t for t in sorted(_tokens(name), key=len, reverse=True) if len(t)>=4][:3]
    if not keys: return []
    hits=[]
    for u in _load_titled():
        ul=u.lower()
        if any(k in ul or (len(k)>=5 and k[:5] in ul) for k in keys):
            hits.append(u)
            if len(hits)>=limit: break
    return hits

def _wiki_photo(name, dest):
    import urllib.parse
    titles=[]
    if "," in name:
        last, first = [x.strip() for x in name.split(",",1)]
        fm = first.split()[0] if first.split() else first
        titles += [f"{fm}_{last}_(chess_player)", f"{first}_{last}_(chess_player)", f"{fm}_{last}"]
    else:
        parts = name.replace("-"," ").split()
        if len(parts)>=2:
            titles += [f"{parts[0]}_{parts[-1]}_(chess_player)", f"{parts[0]}_{parts[-1]}"]
    try:
        q = urllib.parse.quote(name.replace(","," ")+" chess")
        search = _json(f"https://en.wikipedia.org/w/api.php?action=opensearch&search={q}&limit=5&namespace=0&format=json",8)
        if isinstance(search, list) and len(search)>1:
            for title in search[1]: titles.append(title.replace(" ","_"))
    except Exception: pass
    seen=set()
    for title in titles:
        if title.lower() in seen: continue
        seen.add(title.lower())
        try:
            url = "https://en.wikipedia.org/api/rest_v1/page/summary/"+urllib.parse.quote(title.replace(" ","_"))
            req = urllib.request.Request(url, headers={"User-Agent":"Chess64Bot/2.3"})
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            blob = ((data.get("extract") or "")+(data.get("description") or "")).lower()
            if not any(w in blob for w in ("chess","grandmaster","fide")): continue
            thumb = (data.get("originalimage") or {}).get("source") or (data.get("thumbnail") or {}).get("source") or ""
            if not thumb: continue
            req2 = urllib.request.Request(thumb.split("?")[0], headers={"User-Agent":"Chess64Bot/2.3"})
            with urllib.request.urlopen(req2, timeout=15) as r:
                dest.write_bytes(r.read())
            if dest.exists() and dest.stat().st_size>800:
                print(f"  wiki photo: {name!r} <- {data.get('title')}")
                return str(dest)
        except Exception: continue
    return None

def _initials_avatar(name, dest):
    try:
        from PIL import Image, ImageDraw, ImageFont
        parts = re.findall(r"[A-Za-z]+", name or "")
        if not parts: initials="?"
        elif len(parts)==1: initials=parts[0][:2].upper()
        elif "," in (name or ""): initials=(parts[-1][0]+parts[0][0]).upper()
        else: initials=(parts[0][0]+parts[-1][0]).upper()
        size=200
        img=Image.new("RGBA",(size,size),(0,0,0,0))
        draw=ImageDraw.Draw(img)
        draw.ellipse([4,4,size-5,size-5], fill=(18,28,48,255), outline=(201,162,39,255), width=5)
        try: font=ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",72)
        except Exception: font=ImageFont.load_default()
        bb=draw.textbbox((0,0), initials, font=font)
        tw,th=bb[2]-bb[0],bb[3]-bb[1]
        draw.text(((size-tw)/2,(size-th)/2-4), initials, font=font, fill=(255,255,255,255))
        img.convert("RGB").save(dest,"JPEG",quality=90)
        if dest.exists() and dest.stat().st_size>200:
            print(f"  initials avatar: {name!r} -> {initials}")
            return str(dest)
    except Exception as e:
        print(f"  initials fail: {e}")
    return None

def resolve_player_assets(display_name: str) -> Tuple[Optional[str], Optional[str]]:
    players, flags = SCRIPT_DIR/"players", SCRIPT_DIR/"flags"
    players.mkdir(exist_ok=True); flags.mkdir(exist_ok=True)
    name = (display_name or "").strip()
    if not name or name.lower() in ("white","black","?"): return None, None

    cands, seen = [], set()
    for c in _candidates(name)+_titled_cands(name):
        if c.lower() not in seen:
            seen.add(c.lower()); cands.append(c)

    best_prof, best_user, best_score = None, None, 0.0
    known_vals = {v.lower() for v in KNOWN.values()}
    for cand in cands[:20]:
        prof = _fetch(cand)
        if not prof: continue
        if cand.lower() in known_vals:
            best_prof, best_user, best_score = prof, cand, 1.0; break
        sc = _score(name, prof)
        if sc > best_score:
            best_score, best_prof, best_user = sc, prof, cand

    if not best_prof or best_score < 0.34:
        print(f"  no photo match for: {name!r} best={best_score:.2f}")
        safe = re.sub(r"[^a-zA-Z0-9_-]","_", name.lower())[:40]
        dest = players/f"{safe}.jpg"
        photo = _wiki_photo(name, dest) or _initials_avatar(name, dest)
        return photo, None

    print(f"  avatar match: {name!r} -> {best_user} ({best_score:.2f})")
    photo = None
    safe = re.sub(r"[^a-zA-Z0-9_-]","_", (best_user or name).lower())[:40]
    dest = players/f"{safe}.jpg"
    avatar = best_prof.get("avatar")
    if avatar:
        try:
            if not dest.exists() or dest.stat().st_size<500:
                req = urllib.request.Request(avatar, headers={"User-Agent":"Chess64/2.3"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    dest.write_bytes(r.read())
            if dest.exists() and dest.stat().st_size>500:
                photo = str(dest)
        except Exception as e:
            print(f"  avatar download fail: {e}")
    if not photo:
        photo = _wiki_photo(name, dest) or _initials_avatar(name, dest)

    flag = None
    country = (best_prof.get("country") or "").rstrip("/").split("/")[-1].lower()
    if len(country)==2:
        fdest = flags/f"{country}.png"
        if not fdest.exists() or fdest.stat().st_size<50:
            try:
                req = urllib.request.Request(f"https://flagcdn.com/w80/{country}.png", headers={"User-Agent":"Chess64/2.3"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    fdest.write_bytes(r.read())
            except Exception: pass
        if fdest.exists() and fdest.stat().st_size>50:
            flag = str(fdest)
    return photo, flag
