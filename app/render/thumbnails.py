"""Generates viral 16:9 and 9:16 thumbnails from a rendered board frame + title."""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageEnhance

from app.config import settings
from app.utils import fit_text, load_font


def _dramatic_bg(board_frame: Image.Image, size: tuple[int, int]) -> Image.Image:
    bg = board_frame.resize(size).convert("RGB")
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    bg = ImageEnhance.Contrast(bg).enhance(1.15)
    return bg


def _add_title_banner(img: Image.Image, title: str, brand_hashtag: str) -> Image.Image:
    draw = ImageDraw.Draw(img)
    w, h = img.size
    font_size = max(36, w // 14)
    font = load_font(font_size, bold=True)
    line = fit_text(draw, title.upper(), font, w - 60)

    bbox = draw.textbbox((0, 0), line, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = 20
    banner_y = h - th - pad * 3
    draw.rectangle((0, banner_y, w, h), fill=(11, 18, 32, 200))
    draw.text(((w - tw) / 2, banner_y + pad), line, font=font, fill=settings.GOLD)

    brand_font = load_font(max(16, w // 40))
    draw.text((16, 12), brand_hashtag, font=brand_font, fill="#f2e6c9")
    return img


def make_thumbnails(board_frame: Image.Image, title: str, brand_hashtag: str, out_dir: str) -> dict[str, str]:
    wide = _add_title_banner(_dramatic_bg(board_frame, (1280, 720)), title, brand_hashtag)
    tall = _add_title_banner(_dramatic_bg(board_frame, (1080, 1920)), title, brand_hashtag)

    wide_path = f"{out_dir}/thumb_16x9.jpg"
    tall_path = f"{out_dir}/thumb_9x16.jpg"
    wide.convert("RGB").save(wide_path, quality=92)
    tall.convert("RGB").save(tall_path, quality=92)
    return {"wide": wide_path, "tall": tall_path}
