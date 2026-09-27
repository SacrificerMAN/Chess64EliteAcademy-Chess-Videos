"""Patch 07 — Gemini viral prompt + model.

Ensures GEMINI_MODEL defaults to gemini-3.1-flash-lite and that the SEO
system prompt still demands JSON-only output (a regression here would break
every downstream JSON.loads call in app/gemini/client.py).
"""
from __future__ import annotations


def apply() -> None:
    from app.config import settings
    from app.gemini.prompts import SEO_SYSTEM_PROMPT

    if not settings.gemini_model:
        settings.gemini_model = "gemini-3.1-flash-lite"
    assert "JSON" in SEO_SYSTEM_PROMPT, "SEO system prompt must require JSON-only output"
    if not settings.gemini_api_key:
        import logging

        logging.getLogger("chess64.patches").warning(
            "GEMINI_API_KEY not set — SEO metadata will use the local fallback generator."
        )
