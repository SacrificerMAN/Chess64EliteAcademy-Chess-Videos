"""
resolve_player_assets(display_name) -> PlayerAssets

Order of resolution (per spec):
  1. Manual Telegram override (checked by the caller, always wins)
  2. KNOWN_USERNAMES map for well-known GMs -> Chess.com username
  3. Slug-scoring guess against Chess.com's public player search
  4. Wikipedia summary image fallback
  5. Generated initials avatar (always succeeds, so rendering never blocks)
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import httpx
from PIL import Image, ImageDraw

from app.config import settings
from app.utils import initials, load_font, slugify

# A starter map — extend freely. Keys are matched case-insensitively against
# the PGN header name (after removing titles like GM/IM/WGM and reordering
# "Last, First" -> "First Last").
KNOWN_USERNAMES: dict[str, dict[str, str]] = {
    "magnus carlsen": {"chesscom": "magnuscarlsen", "flag": "NO"},
    "hikaru nakamura": {"chesscom": "hikaru", "flag": "US"},
    "fabiano caruana": {"chesscom": "fabianocaruana", "flag": "US"},
    "praggnanandhaa r": {"chesscom": "rpragchess", "flag": "IN"},
    "r praggnanandhaa": {"chesscom": "rpragchess", "flag": "IN"},
    "ding liren": {"chesscom": "dingliren", "flag": "CN"},
    "gukesh d": {"chesscom": "gukeshdommaraju", "flag": "IN"},
    "ian nepomniachtchi": {"chesscom": "lachesisq", "flag": "RU"},
    "alireza firouzja": {"chesscom": "firouzja2003", "flag": "FR"},
    "viswanathan anand": {"chesscom": "vishy64theking", "flag": "IN"},
    "wesley so": {"chesscom": "gmwso", "flag": "US"},
    "levon aronian": {"chesscom": "levaronian", "flag": "US"},
    "anish giri": {"chesscom": "anishgiri", "flag": "NL"},
}


@dataclass
class PlayerAssets:
    display_name: str
    avatar_image: Image.Image
    country_code: str | None
    source: str  # known|chesscom_search|wikipedia|initials|manual


def _normalize_name(name: str) -> str:
    name = name.strip()
    for title in ("GM ", "IM ", "WGM ", "WIM ", "FM ", "CM "):
        if name.upper().startswith(title.strip().upper() + " "):
            name = name[len(title):]
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
        name = f"{first} {last}"
    return name


def _fetch_image(url: str, timeout: float = 6.0) -> Image.Image | None:
    try:
        resp = httpx.get(url, timeout=timeout, follow_redirects=True)
        if resp.status_code == 200 and resp.content:
            return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception:
        return None
    return None


def _chesscom_lookup(username: str) -> tuple[Image.Image | None, str | None]:
    try:
        prof = httpx.get(f"https://api.chess.com/pub/player/{username}", timeout=6.0)
        if prof.status_code != 200:
            return None, None
        j = prof.json()
        avatar_url = j.get("avatar")
        country_url = j.get("country")  # e.g. https://api.chess.com/pub/country/IN
        country_code = None
        if country_url:
            code = country_url.rstrip("/").split("/")[-1]
            country_code = code
        img = _fetch_image(avatar_url) if avatar_url else None
        return img, country_code
    except Exception:
        return None, None


def _chesscom_search_guess(name: str) -> str | None:
    """Best-effort slug scoring against likely Chess.com usernames."""
    candidates = [
        slugify(name),
        slugify(name.replace(" ", "")),
        slugify("gm" + name.replace(" ", "")),
    ]
    parts = name.split()
    if len(parts) >= 2:
        candidates.append(slugify(parts[0][0] + parts[-1]))  # e.g. mcarlsen
    for candidate in candidates:
        img, _ = _chesscom_lookup(candidate)
        if img is not None:
            return candidate
    return None


def _wikipedia_fallback(name: str) -> Image.Image | None:
    try:
        resp = httpx.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{name.replace(' ', '_')}",
            timeout=6.0,
        )
        if resp.status_code == 200:
            j = resp.json()
            thumb = (j.get("thumbnail") or {}).get("source")
            if thumb:
                return _fetch_image(thumb)
    except Exception:
        return None
    return None


def _generate_initials_avatar(name: str, size: int = 256) -> Image.Image:
    img = Image.new("RGBA", (size, size), settings.NAVY_BG)
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size, size), fill="#1b2a4a", outline=settings.GOLD, width=6)
    font = load_font(size // 3, bold=True)
    text = initials(name)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]), text, font=font, fill="#f2e6c9")
    return img


def resolve_player_assets(display_name: str) -> PlayerAssets:
    name = _normalize_name(display_name)
    key = name.lower()

    if key in KNOWN_USERNAMES:
        entry = KNOWN_USERNAMES[key]
        img, cc = _chesscom_lookup(entry["chesscom"])
        cc = cc or entry.get("flag")
        if img is not None:
            return PlayerAssets(name, img, cc, "known")

    guess = _chesscom_search_guess(name)
    if guess:
        img, cc = _chesscom_lookup(guess)
        if img is not None:
            return PlayerAssets(name, img, cc, "chesscom_search")

    wiki_img = _wikipedia_fallback(name)
    if wiki_img is not None:
        return PlayerAssets(name, wiki_img, None, "wikipedia")

    return PlayerAssets(name, _generate_initials_avatar(name), None, "initials")
