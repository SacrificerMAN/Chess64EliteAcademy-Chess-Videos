"""Optional voice commentary via edge-tts (free Microsoft neural voices)."""
from __future__ import annotations

import asyncio
import logging

import edge_tts

logger = logging.getLogger("chess64.tts")

DEFAULT_VOICE = "en-US-ChristopherNeural"
DEFAULT_RATE = "+8%"  # "slightly up" per spec


async def _synthesize(text: str, out_path: str, voice: str, rate: str) -> None:
    communicate = edge_tts.Communicate(text, voice=voice, rate=rate)
    await communicate.save(out_path)


def synthesize_commentary(lines: list[dict], out_path: str, voice: str = DEFAULT_VOICE,
                           rate: str = DEFAULT_RATE) -> str | None:
    """
    lines: [{"ply": int, "line": str}, ...] (empty "line" entries are skipped)
    Returns the audio path, or None if synthesis failed (fail soft — video
    still renders silent).
    """
    script = " ... ".join(l["line"] for l in lines if l.get("line"))
    if not script.strip():
        return None
    try:
        asyncio.run(_synthesize(script, out_path, voice, rate))
        return out_path
    except Exception as exc:
        logger.warning("TTS synthesis failed, continuing with silent video: %s", exc)
        return None
