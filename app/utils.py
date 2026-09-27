"""Small shared helpers used across rendering and bot modules."""
from __future__ import annotations

import re
import unicodedata
from PIL import Image, ImageDraw, ImageFont

from app.config import settings


def even(n: int) -> int:
    """Round down to the nearest even number (FFmpeg yuv420p requirement)."""
    return n if n % 2 == 0 else n - 1


def normalize_frame(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """
    Force every frame to identical even dimensions before handing to FFmpeg.
    Prevents the classic "Broken pipe" from mismatched frame sizes.
    """
    target_w, target_h = even(target_w), even(target_h)
    if img.size != (target_w, target_h):
        canvas = Image.new("RGB", (target_w, target_h), settings.NAVY_BG)
        # center-fit
        img_ratio = img.width / img.height
        tgt_ratio = target_w / target_h
        if img_ratio > tgt_ratio:
            new_w = target_w
            new_h = int(target_w / img_ratio)
        else:
            new_h = target_h
            new_w = int(target_h * img_ratio)
        resized = img.resize((max(new_w, 2), max(new_h, 2)))
        canvas.paste(resized, ((target_w - resized.width) // 2, (target_h - resized.height) // 2))
        return canvas
    return img.convert("RGB")


def country_to_flag_emoji(cc: str) -> str:
    """Convert a 2-letter ISO country code into a flag emoji (used in captions)."""
    cc = cc.strip().upper()
    if len(cc) != 2 or not cc.isalpha():
        return "🏳️"
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in cc)


def slugify(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r"[^a-zA-Z0-9]+", "", name)
    return name.lower()


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Load a bundled font, falling back to PIL's default bitmap font if the
    asset isn't present (keeps rendering functional even with a bare-bones
    container image before assets are baked in).
    """
    import os

    name = "Inter-Bold.ttf" if bold else "Inter-Regular.ttf"
    path = os.path.join(settings.assets_dir, "fonts", name)
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def fit_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> str:
    """Truncate text with an ellipsis so it fits max_width at the given font."""
    if draw.textlength(text, font=font) <= max_width:
        return text
    while text and draw.textlength(text + "…", font=font) > max_width:
        text = text[:-1]
    return text + "…"


def initials(name: str) -> str:
    parts = [p for p in re.split(r"\s+", name.strip()) if p]
    if not parts:
        return "??"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()
