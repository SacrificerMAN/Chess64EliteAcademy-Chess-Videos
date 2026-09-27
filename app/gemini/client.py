"""
Minimal REST client for the Gemini Generative Language API. Kept dependency-
free (httpx only) so it works the same locally and on Railway.
"""
from __future__ import annotations

import json
import logging

import httpx

from app.analysis import GameData
from app.config import settings
from app.gemini.prompts import (
    BRAND_FOOTER,
    SEO_SYSTEM_PROMPT,
    build_seo_user_prompt,
    build_commentary_user_prompt,
    commentary_system_prompt,
)

logger = logging.getLogger("chess64.gemini")

API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
    return text.strip()


def _call_gemini(system_prompt: str, user_prompt: str, json_mode: bool = True) -> str:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    url = f"{API_BASE}/{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "response_mime_type": "application/json" if json_mode else "text/plain",
        },
    }
    resp = httpx.post(url, json=payload, timeout=30.0)
    resp.raise_for_status()
    j = resp.json()
    return j["candidates"][0]["content"]["parts"][0]["text"]


def _local_fallback_seo(game: GameData) -> dict:
    """Deterministic, non-LLM fallback so a Gemini outage never blocks a job."""
    verb = "DESTROYS" if game.result in ("1-0", "0-1") else "BATTLES"
    title = f"{game.white} {verb} {game.black} — Chess Masterclass"[:89]
    hi_title = f"{game.white} ने {game.black} को हराया — शतरंज मास्टरक्लास"[:89]
    return {
        "hook": f"Watch {game.white} outplay {game.black} move by move!",
        "hook_hi": f"{game.white} ने कैसे {game.black} को मात दी, देखिए!",
        "title": title,
        "title_hi": hi_title,
        "shorts_title": title[:49],
        "shorts_title_hi": hi_title[:49],
        "title_options": [title],
        "title_options_hi": [hi_title],
        "description": (
            f"A full breakdown of {game.white} vs {game.black}"
            f"{' at ' + game.event if game.event else ''}. Learn the key ideas, "
            f"tactics, and turning points in this game, explained simply for "
            f"club players. Subscribe for daily GM games and traps!"
        ),
        "description_hi": (
            f"{game.white} बनाम {game.black} की पूरी व्याख्या। सीखिए मुख्य विचार, "
            f"रणनीति और निर्णायक क्षण, आसान भाषा में। रोज़ नई GM गेम्स के लिए सब्सक्राइब करें!"
        ),
        "hashtags": [settings.brand_hashtag, "#Chess", "#Grandmaster", "#ChessTactics"],
        "tags": [
            "chess", "chess game", "grandmaster chess", game.white.lower(), game.black.lower(),
            "chess tactics", "chess traps", "chess masterclass", "chess strategy",
            "learn chess", "chess opening", "chess endgame", "chess sacrifice",
            "chess brilliancy", "chess analysis", "chess lesson", "chess for beginners",
            "hindi chess", "chess hindi", "chess highlights",
        ],
        "source": "local_fallback",
    }


def generate_seo_metadata(game: GameData) -> dict:
    moves_list = ", ".join(m.san for m in game.moves)
    try:
        raw = _call_gemini(SEO_SYSTEM_PROMPT, build_seo_user_prompt(game, moves_list))
        meta = json.loads(_strip_code_fences(raw))
        meta["source"] = "gemini"
    except Exception as exc:
        logger.warning("Gemini SEO call failed (%s); using local fallback.", exc)
        meta = _local_fallback_seo(game)

    # append brand footer + guard against banned score-in-title patterns
    meta["description"] = (meta.get("description", "") + BRAND_FOOTER).strip()
    meta["description_hi"] = (meta.get("description_hi", "") + BRAND_FOOTER).strip()
    for key in ("title", "title_hi", "shorts_title", "shorts_title_hi"):
        meta[key] = _scrub_score(meta.get(key, ""))
    meta["title_options"] = [_scrub_score(t) for t in meta.get("title_options", [])]
    meta["title_options_hi"] = [_scrub_score(t) for t in meta.get("title_options_hi", [])]
    if settings.brand_hashtag not in meta.get("hashtags", []):
        meta.setdefault("hashtags", []).append(settings.brand_hashtag)
    return meta


def _scrub_score(title: str) -> str:
    import re

    return re.sub(r"\b[01](/2)?-[01](/2)?\b", "", title).strip()


def generate_commentary(game: GameData, short: bool) -> list[dict]:
    try:
        raw = _call_gemini(
            commentary_system_prompt(short),
            build_commentary_user_prompt(game, short),
        )
        return json.loads(_strip_code_fences(raw))
    except Exception as exc:
        logger.warning("Gemini commentary call failed (%s); commentary disabled for this job.", exc)
        return []
