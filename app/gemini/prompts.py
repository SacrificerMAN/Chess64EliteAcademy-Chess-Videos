"""Prompt templates matching the Chess64 Elite Academy SEO/commentary spec."""
from __future__ import annotations

from app.analysis import GameData
from app.config import settings

SEO_SYSTEM_PROMPT = (
    "You are an elite viral chess YouTube growth expert (GothamChess energy, "
    "Indian + global SEO). Return ONLY valid JSON, no markdown, no code fences, "
    "no commentary before or after the JSON."
)

SEO_JSON_KEYS = (
    "hook, hook_hi, title, title_hi, shorts_title, shorts_title_hi, "
    "title_options[], title_options_hi[], description (500-900 chars + CTA), "
    "description_hi, hashtags[] (must include #Chess64EliteAcademy), "
    "tags[] (20-25, no #)"
)

BRAND_FOOTER = (
    "\n\n♟ Chess64 Elite Academy\n"
    "Daily GM games · Traps · Hindi + English\n"
    f"🔔 Subscribe | 📱 {settings.telegram_channel_url}\n"
    f"{settings.brand_hashtag} #Chess #Grandmaster"
)


def build_seo_user_prompt(game: GameData, moves_list: str) -> str:
    return f"""Channel: {settings.channel_name}
White: {game.white}
Black: {game.black}
Result: {game.result}
Event: {game.event or "N/A"}
ECO: {game.eco or "N/A"}
Platform: {game.platform}
Moves: {moves_list}

Write MAXIMUM-CLICK titles:
- Power words: DESTROYS, BRILLIANT, INSANE, SHOCKING, MASTERCLASS, TRAP, SACRIFICE
- Use famous surnames + big events when relevant
- Do NOT include the final score (e.g. 1-0, 0-1, 1/2-1/2) anywhere in any title
- Main title under 90 characters; Shorts title under 50 characters
- Titles must reference a specific moment or verb (e.g. "Carlsen's Queen Sac
  DESTROYS the Sicilian"), never generic filler like "Ultimate Clash"

Return ONLY a JSON object with these exact keys: {SEO_JSON_KEYS}
The "description" and "description_hi" fields should NOT include the brand
footer — it is appended automatically after generation.
"""


def commentary_system_prompt(short: bool) -> str:
    if short:
        return (
            "You are an energetic chess YouTube Shorts narrator. Write ONLY the "
            "critical moments of the game in 120-200 words total. For quiet, "
            "non-critical moves, contribute an empty string. No spoilers before "
            "the critical moment happens. High energy, GothamChess-style teaching "
            "tone. Return ONLY valid JSON: a list of {\"ply\": int, \"line\": str}."
        )
    return (
        "You are an energetic chess YouTube commentator narrating a full game "
        "for 800-1600 rated players, GothamChess-style. Write one commentary "
        "line per move (roughly 1200-1700 words total for the whole game). "
        "Explain plans and tactics simply. Do not reveal the final result or "
        "upcoming brilliancies before they happen. Return ONLY valid JSON: a "
        "list of {\"ply\": int, \"line\": str}, one entry per move in order."
    )


def build_commentary_user_prompt(game: GameData, short: bool) -> str:
    moves = "\n".join(f"{m.ply}. {m.san}" for m in game.moves)
    label = "Shorts" if short else "Long-form"
    return f"""Game: {game.white} vs {game.black} ({game.result}), {game.event or "casual"}.
Format: {label} commentary.
Moves:
{moves}
"""
