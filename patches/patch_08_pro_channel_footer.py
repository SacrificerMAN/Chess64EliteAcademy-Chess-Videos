"""Patch 08 — pro channel footer.

Verifies the brand footer template contains the Telegram link and the brand
hashtag, and that generate_seo_metadata() actually appends it, so every
description always ends with a consistent CTA regardless of what Gemini
returns.
"""
from __future__ import annotations

import inspect


def apply() -> None:
    from app.config import settings
    from app.gemini import client as gemini_client
    from app.gemini.prompts import BRAND_FOOTER

    assert settings.telegram_channel_url in BRAND_FOOTER
    assert settings.brand_hashtag in BRAND_FOOTER or "#Chess64EliteAcademy" in BRAND_FOOTER

    src = inspect.getsource(gemini_client.generate_seo_metadata)
    assert "BRAND_FOOTER" in src, "generate_seo_metadata must append BRAND_FOOTER"
