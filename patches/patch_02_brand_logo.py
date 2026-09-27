"""Patch 02 — brand logo watermark.

Ensures a Chess64 logo watermark asset exists at assets/brand/logo.png.
If missing (e.g. fresh checkout before the real logo is committed), generates
a simple placeholder gold-on-navy wordmark so rendering never breaks for
lack of a logo file.
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw

from app.config import settings
from app.utils import load_font


def apply() -> None:
    brand_dir = os.path.join(settings.assets_dir, "brand")
    os.makedirs(brand_dir, exist_ok=True)
    logo_path = os.path.join(brand_dir, "logo.png")
    if os.path.exists(logo_path):
        return

    img = Image.new("RGBA", (400, 120), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_font(40, bold=True)
    draw.text((10, 35), "Chess64", font=font, fill=settings.GOLD)
    img.save(logo_path)
