"""
Famous Traps — vertical educational style.
Bigger title, Like & Subscribe CTA, Chess64 Elite Academy branding.
Board palette from reference: light #3A473E / dark #222824 / gold #F8D942
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

BG = "#0B0C0E"
SQ_LIGHT = "#3A473E"
SQ_DARK = "#222824"
TITLE_YELLOW = "#F8D942"
MOVE_YELLOW = "#F2D84C"
ARROW_YELLOW = "#F9CA26"
HIGHLIGHT = "#C4A32A"
BRAND_WHITE = "#F5F0E1"
CTA_GOLD = "#FFD54A"

BRAND_NAME = "Chess64 Elite Academy"
CTA_TEXT = "Like & Subscribe"


@dataclass
class TrapRenderContext:
    series_title: str = "Famous Traps"
    trap_name: str = ""
    theme: str = "ref_green"


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
        "coord": "#6A7A6A",
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
        coordinates=False,
    )
    png_bytes = cairosvg.svg2png(
        bytestring=svg_data.encode("utf-8"),
        output_width=size,
        output_height=size,
    )
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def _draw_branding(draw: ImageDraw.ImageDraw, canvas_h: int = TRAP_H) -> None:
    """Bottom CTA + channel name branding."""
    cta_font = load_font(36, bold=True)
    brand_font = load_font(28, bold=True)

    cta = CTA_TEXT
    bbox = draw.textbbox((0, 0), cta, font=cta_font)
    cw = bbox[2] - bbox[0]
    cta_y = canvas_h - 140
    draw.text(((TRAP_W - cw) / 2, cta_y), cta, font=cta_font, fill=CTA_GOLD)

    brand = BRAND_NAME
    bbox2 = draw.textbbox((0, 0), brand, font=brand_font)
    bw = bbox2[2] - bbox2[0]
    brand_y = cta_y + 48
    draw.text(((TRAP_W - bw) / 2, brand_y), brand, font=brand_font, fill=BRAND_WHITE)


def render_trap_frame(
    ctx: TrapRenderContext,
    board: chess.Board,
    last_move: chess.Move | None,
    move_label: str,
) -> Image.Image:
    canvas = Image.new("RGB", (TRAP_W, TRAP_H), BG)
    draw = ImageDraw.Draw(canvas)

    # Bigger title
    title_font = load_font(96, bold=True)
    title = ctx.series_title or "Famous Traps"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    title_y = 110
    draw.text(((TRAP_W - tw) / 2, title_y), title, font=title_font, fill=TITLE_YELLOW)

    # Board centered with room for bottom branding
    board_px = even(860)
    board_img = _board_to_pil(board, board_px, last_move, last_move)
    bx = (TRAP_W - board_px) // 2
    by = 260
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(board_img, (bx, by), board_img)
    canvas = canvas_rgba.convert("RGB")
    draw = ImageDraw.Draw(canvas)

    if move_label:
        move_font = load_font(40, bold=True)
        label = fit_text(draw, move_label, move_font, TRAP_W - 80)
        bbox3 = draw.textbbox((0, 0), label, font=move_font)
        mw = bbox3[2] - bbox3[0]
        my = by + board_px + 28
        draw.text(((TRAP_W - mw) / 2, my), label, font=move_font, fill=MOVE_YELLOW)

    _draw_branding(draw)
    return normalize_frame(canvas, TRAP_W, TRAP_H)


def trap_intro_card(ctx: TrapRenderContext) -> Image.Image:
    """Starting position + big title + branding."""
    canvas = Image.new("RGB", (TRAP_W, TRAP_H), BG)
    draw = ImageDraw.Draw(canvas)

    title_font = load_font(96, bold=True)
    title = ctx.series_title or "Famous Traps"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    title_y = 110
    draw.text(((TRAP_W - tw) / 2, title_y), title, font=title_font, fill=TITLE_YELLOW)

    board = chess.Board()
    board_px = even(860)
    board_img = _board_to_pil(board, board_px, last_move=None, arrow_move=None)
    bx = (TRAP_W - board_px) // 2
    by = 260
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(board_img, (bx, by), board_img)
    canvas = canvas_rgba.convert("RGB")
    draw = ImageDraw.Draw(canvas)

    _draw_branding(draw)
    return normalize_frame(canvas, TRAP_W, TRAP_H)


def format_san_label(ply_index: int, san: str) -> str:
    move_num = ply_index // 2 + 1
    if ply_index % 2 == 0:
        return f"{move_num}. {san}"
    return f"{move_num}... {san}"
