"""
Famous Traps style — matches reference educational Shorts:
  pure dark canvas, LARGE bright yellow title, dark-theme board,
  yellow arrows + last-move highlights, SAN under board.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import cairosvg
import chess
import chess.svg
from PIL import Image, ImageDraw

from app.config import settings
from app.utils import even, fit_text, load_font, normalize_frame

TRAP_W, TRAP_H = 1080, 1920
TITLE_YELLOW = "#FFD54F"
MOVE_YELLOW = "#FFD54F"
ARROW_YELLOW = "#F5C518"
HIGHLIGHT = "#C9A227"
BG = "#0A0A0A"
SQ_LIGHT = "#4A4A4A"
SQ_DARK = "#2B2B2B"


@dataclass
class TrapRenderContext:
    series_title: str = "Famous Traps"
    trap_name: str = ""
    theme: str = "dark"


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
        "margin": "#0A0A0A",
        "coord": "#888888",
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
    png_bytes = cairosvg.svg2png(
        bytestring=svg_data.encode("utf-8"),
        output_width=size,
        output_height=size,
    )
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def render_trap_frame(
    ctx: TrapRenderContext,
    board: chess.Board,
    last_move: chess.Move | None,
    move_label: str,
) -> Image.Image:
    canvas = Image.new("RGB", (TRAP_W, TRAP_H), BG)
    draw = ImageDraw.Draw(canvas)

    # BIG bright series title — reference size
    title_font = load_font(120, bold=True)
    title = ctx.series_title or "Famous Traps"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    title_y = 50
    draw.text(((TRAP_W - tw) / 2, title_y), title, font=title_font, fill=TITLE_YELLOW)

    # Trap name under title
    if ctx.trap_name:
        sub_font = load_font(36)
        sub = fit_text(draw, ctx.trap_name, sub_font, TRAP_W - 80)
        bbox2 = draw.textbbox((0, 0), sub, font=sub_font)
        sw = bbox2[2] - bbox2[0]
        sub_y = title_y + th + 24
        draw.text(((TRAP_W - sw) / 2, sub_y), sub, font=sub_font, fill="#CCCCCC")
        board_top = sub_y + 50
    else:
        board_top = title_y + th + 36

    # Board — slightly smaller so title has room
    board_px = even(min(960, TRAP_W - 80))
    board_img = _board_to_pil(board, board_px, last_move, last_move)
    bx = (TRAP_W - board_px) // 2
    by = max(board_top, 200)
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(board_img, (bx, by), board_img)
    canvas = canvas_rgba.convert("RGB")
    draw = ImageDraw.Draw(canvas)

    if move_label:
        move_font = load_font(56, bold=True)
        label = fit_text(draw, move_label, move_font, TRAP_W - 80)
        bbox3 = draw.textbbox((0, 0), label, font=move_font)
        mw = bbox3[2] - bbox3[0]
        my = by + board_px + 36
        draw.text(((TRAP_W - mw) / 2, my), label, font=move_font, fill=MOVE_YELLOW)

    brand_font = load_font(22)
    brand = settings.brand_hashtag
    bbox4 = draw.textbbox((0, 0), brand, font=brand_font)
    bw = bbox4[2] - bbox4[0]
    draw.text(((TRAP_W - bw) / 2, TRAP_H - 55), brand, font=brand_font, fill="#444444")

    return normalize_frame(canvas, TRAP_W, TRAP_H)


def trap_intro_card(ctx: TrapRenderContext) -> Image.Image:
    canvas = Image.new("RGB", (TRAP_W, TRAP_H), BG)
    draw = ImageDraw.Draw(canvas)

    # Extra-large intro title
    title_font = load_font(140, bold=True)
    title = ctx.series_title or "Famous Traps"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((TRAP_W - tw) / 2, TRAP_H / 2 - th - 40), title, font=title_font, fill=TITLE_YELLOW)

    if ctx.trap_name:
        sub_font = load_font(48)
        sub = fit_text(draw, ctx.trap_name, sub_font, TRAP_W - 100)
        bbox2 = draw.textbbox((0, 0), sub, font=sub_font)
        sw = bbox2[2] - bbox2[0]
        draw.text(((TRAP_W - sw) / 2, TRAP_H / 2 + 30), sub, font=sub_font, fill="#DDDDDD")

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
