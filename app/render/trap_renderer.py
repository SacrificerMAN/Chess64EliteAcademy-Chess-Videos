"""
Famous Traps style — pixel-match reference educational Shorts:
  soft gold title, dark-green board, clean yellow arrows + square highlights,
  SAN under board, generous black margins (9:16).
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

# Reference palette (from vOew1 frames)
TITLE_YELLOW = "#E8C84A"   # soft gold, not neon
MOVE_YELLOW = "#E8C84A"
ARROW_YELLOW = "#E8C84A"
HIGHLIGHT = "#C9A84C"      # muted gold last-move squares
BG = "#0D0D0D"
# Dark green board (reference) — not charcoal gray
SQ_LIGHT = "#5A6B52"
SQ_DARK = "#3A4636"


@dataclass
class TrapRenderContext:
    series_title: str = "Famous Traps"
    trap_name: str = ""
    theme: str = "dark_green"


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
        "coord": "#8A9A82",
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
        coordinates=False,  # reference has no a-h / 1-8 labels
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

    # Soft gold title — reference size (~72px), centered, clean (no glow)
    title_font = load_font(72, bold=True)
    title = ctx.series_title or "Famous Traps"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    title_y = 120
    draw.text(((TRAP_W - tw) / 2, title_y), title, font=title_font, fill=TITLE_YELLOW)

    # Board: generous top/bottom black space like reference
    board_px = even(min(900, TRAP_W - 120))
    board_img = _board_to_pil(board, board_px, last_move, last_move)
    bx = (TRAP_W - board_px) // 2
    by = title_y + th + 56
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(board_img, (bx, by), board_img)
    canvas = canvas_rgba.convert("RGB")
    draw = ImageDraw.Draw(canvas)

    # SAN under board
    if move_label:
        move_font = load_font(42, bold=True)
        label = fit_text(draw, move_label, move_font, TRAP_W - 80)
        bbox3 = draw.textbbox((0, 0), label, font=move_font)
        mw = bbox3[2] - bbox3[0]
        my = by + board_px + 28
        draw.text(((TRAP_W - mw) / 2, my), label, font=move_font, fill=MOVE_YELLOW)

    return normalize_frame(canvas, TRAP_W, TRAP_H)


def trap_intro_card(ctx: TrapRenderContext) -> Image.Image:
    """Opening board (starting position) + title — matches reference first frame."""
    canvas = Image.new("RGB", (TRAP_W, TRAP_H), BG)
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(72, bold=True)
    title = ctx.series_title or "Famous Traps"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    title_y = 120
    draw.text(((TRAP_W - tw) / 2, title_y), title, font=title_font, fill=TITLE_YELLOW)

    board = chess.Board()
    board_px = even(min(900, TRAP_W - 120))
    board_img = _board_to_pil(board, board_px, last_move=None, arrow_move=None)
    bx = (TRAP_W - board_px) // 2
    by = title_y + th + 56
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(board_img, (bx, by), board_img)
    canvas = canvas_rgba.convert("RGB")

    return normalize_frame(canvas, TRAP_W, TRAP_H)


def format_san_label(ply_index: int, san: str) -> str:
    move_num = ply_index // 2 + 1
    if ply_index % 2 == 0:
        return f"{move_num}. {san}"
    return f"{move_num}... {san}"
