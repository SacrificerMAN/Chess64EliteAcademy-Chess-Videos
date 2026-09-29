"""
Famous Traps style — clean educational Shorts matching reference:
  pure dark canvas, LARGE bright yellow title, dark board,
  thick vivid yellow arrows + gold last-move highlights, SAN under board.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass

import cairosvg
import chess
import chess.svg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.config import settings
from app.utils import even, fit_text, load_font, normalize_frame

TRAP_W, TRAP_H = 1080, 1920
# Vivid bright yellow (reference pop)
TITLE_YELLOW = "#FFCC00"
MOVE_YELLOW = "#FFCC00"
ARROW_YELLOW = "#FFCC00"
HIGHLIGHT = "#E6B800"
BG = "#0A0A0A"
SQ_LIGHT = "#3D3D3D"
SQ_DARK = "#262626"


@dataclass
class TrapRenderContext:
    series_title: str = "Famous Traps"
    trap_name: str = ""
    theme: str = "dark"


def _thicken_arrows(svg: str, factor: float = 1.55) -> str:
    """Boost arrow stroke-width so arrows read clearly on dark board."""
    def _bump(m: re.Match) -> str:
        w = float(m.group(1)) * factor
        return f'stroke-width="{w:.1f}"'
    return re.sub(r'stroke-width="([\d.]+)"(?=[^>]*class="arrow")', _bump, svg)


def _board_to_pil(
    board: chess.Board,
    size: int,
    last_move: chess.Move | None,
    arrow_move: chess.Move | None,
) -> Image.Image:
    fill = {
        "square light": SQ_LIGHT,
        "square dark": SQ_DARK,
        "square light lastmove": HIGHLIGHT,
        "square dark lastmove": HIGHLIGHT,
        "margin": BG,
        "coord": "#9A9A9A",
    }
    arrows = []
    if arrow_move:
        arrows.append(
            chess.svg.Arrow(
                arrow_move.from_square,
                arrow_move.to_square,
                color=ARROW_YELLOW,
            )
        )
    svg_data = chess.svg.board(
        board,
        size=size,
        lastmove=last_move,
        colors=fill,
        arrows=arrows,
        coordinates=True,
    )
    if arrows:
        svg_data = _thicken_arrows(svg_data, factor=1.6)
    png_bytes = cairosvg.svg2png(
        bytestring=svg_data.encode("utf-8"),
        output_width=size,
        output_height=size,
    )
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def _draw_title_glow(
    canvas: Image.Image,
    text: str,
    font: ImageFont.ImageFont,
    xy: tuple[float, float],
    fill: str,
) -> None:
    """Draw bright title with soft glow for reference-style pop."""
    # Glow layer
    glow = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.text(xy, text, font=font, fill=(255, 204, 0, 140))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=8))
    base = canvas.convert("RGBA")
    base = Image.alpha_composite(base, glow)
    # Crisp text on top
    draw = ImageDraw.Draw(base)
    draw.text(xy, text, font=font, fill=fill)
    canvas.paste(base.convert("RGB"))


def render_trap_frame(
    ctx: TrapRenderContext,
    board: chess.Board,
    last_move: chess.Move | None,
    move_label: str,
) -> Image.Image:
    canvas = Image.new("RGB", (TRAP_W, TRAP_H), BG)
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(120, bold=True)
    title = ctx.series_title or "Famous Traps"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    title_x = (TRAP_W - tw) / 2
    title_y = 48
    _draw_title_glow(canvas, title, title_font, (title_x, title_y), TITLE_YELLOW)
    draw = ImageDraw.Draw(canvas)

    if ctx.trap_name:
        sub_font = load_font(34)
        sub = fit_text(draw, ctx.trap_name, sub_font, TRAP_W - 80)
        bbox2 = draw.textbbox((0, 0), sub, font=sub_font)
        sw = bbox2[2] - bbox2[0]
        sub_y = title_y + th + 18
        draw.text(((TRAP_W - sw) / 2, sub_y), sub, font=sub_font, fill="#D0D0D0")
        board_top = sub_y + 44
    else:
        board_top = title_y + th + 28

    board_px = even(min(960, TRAP_W - 80))
    board_img = _board_to_pil(board, board_px, last_move, last_move)
    bx = (TRAP_W - board_px) // 2
    by = max(int(board_top), 200)
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(board_img, (bx, by), board_img)
    canvas = canvas_rgba.convert("RGB")
    draw = ImageDraw.Draw(canvas)

    if move_label:
        move_font = load_font(56, bold=True)
        label = fit_text(draw, move_label, move_font, TRAP_W - 80)
        bbox3 = draw.textbbox((0, 0), label, font=move_font)
        mw = bbox3[2] - bbox3[0]
        my = by + board_px + 32
        # slight glow on SAN too
        _draw_title_glow(canvas, label, move_font, ((TRAP_W - mw) / 2, my), MOVE_YELLOW)
        draw = ImageDraw.Draw(canvas)

    brand_font = load_font(22)
    brand = settings.brand_hashtag
    bbox4 = draw.textbbox((0, 0), brand, font=brand_font)
    bw = bbox4[2] - bbox4[0]
    draw.text(((TRAP_W - bw) / 2, TRAP_H - 55), brand, font=brand_font, fill="#444444")

    return normalize_frame(canvas, TRAP_W, TRAP_H)


def trap_intro_card(ctx: TrapRenderContext) -> Image.Image:
    canvas = Image.new("RGB", (TRAP_W, TRAP_H), BG)
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(140, bold=True)
    title = ctx.series_title or "Famous Traps"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (TRAP_W - tw) / 2
    ty = TRAP_H / 2 - th - 40
    _draw_title_glow(canvas, title, title_font, (tx, ty), TITLE_YELLOW)
    draw = ImageDraw.Draw(canvas)

    if ctx.trap_name:
        sub_font = load_font(46)
        sub = fit_text(draw, ctx.trap_name, sub_font, TRAP_W - 100)
        bbox2 = draw.textbbox((0, 0), sub, font=sub_font)
        sw = bbox2[2] - bbox2[0]
        draw.text(((TRAP_W - sw) / 2, TRAP_H / 2 + 28), sub, font=sub_font, fill="#E0E0E0")

    brand_font = load_font(26)
    brand = settings.brand_hashtag
    bbox3 = draw.textbbox((0, 0), brand, font=brand_font)
    bw = bbox3[2] - bbox3[0]
    draw.text(((TRAP_W - bw) / 2, TRAP_H - 80), brand, font=brand_font, fill="#555555")
    return normalize_frame(canvas, TRAP_W, TRAP_H)


def format_san_label(ply_index: int, san: str) -> str:
    move_num = ply_index // 2 + 1
    if ply_index % 2 == 0:
        return f"{move_num}. {san}"
    return f"{move_num}... {san}"
