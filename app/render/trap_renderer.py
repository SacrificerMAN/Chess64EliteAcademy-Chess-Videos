"""
Famous Traps style renderer — clean educational Shorts look:
  pure dark canvas, yellow series title, centered board with yellow arrows
  + last-move highlights, SAN move text under the board.
No player photos, flags, clocks, or gold studio frame.
Default canvas is 9:16 (1080x1920) for Reels/Shorts.
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
TITLE_YELLOW = "#F5D76E"
MOVE_YELLOW = "#F5D76E"
ARROW_YELLOW = "#F5C518"
HIGHLIGHT = "#E8C84A"
BG = "#0A0A0A"
SQ_LIGHT = "#eeeed2"
SQ_DARK = "#769656"


@dataclass
class TrapRenderContext:
    series_title: str = "Famous Traps"
    trap_name: str = ""
    theme: str = "green"


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

    title_font = load_font(64, bold=True)
    title = ctx.series_title or "Famous Traps"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((TRAP_W - tw) / 2, 80), title, font=title_font, fill=TITLE_YELLOW)

    if ctx.trap_name:
        sub_font = load_font(28)
        sub = fit_text(draw, ctx.trap_name, sub_font, TRAP_W - 80)
        bbox2 = draw.textbbox((0, 0), sub, font=sub_font)
        sw = bbox2[2] - bbox2[0]
        draw.text(((TRAP_W - sw) / 2, 160), sub, font=sub_font, fill="#AAAAAA")

    board_px = even(min(980, TRAP_W - 80))
    board_img = _board_to_pil(board, board_px, last_move, last_move)
    bx = (TRAP_W - board_px) // 2
    by = 220
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(board_img, (bx, by), board_img)
    canvas = canvas_rgba.convert("RGB")
    draw = ImageDraw.Draw(canvas)

    if move_label:
        move_font = load_font(48, bold=True)
        label = fit_text(draw, move_label, move_font, TRAP_W - 80)
        bbox3 = draw.textbbox((0, 0), label, font=move_font)
        mw = bbox3[2] - bbox3[0]
        my = by + board_px + 36
        draw.text(((TRAP_W - mw) / 2, my), label, font=move_font, fill=MOVE_YELLOW)

    brand_font = load_font(22)
    brand = settings.brand_hashtag
    bbox4 = draw.textbbox((0, 0), brand, font=brand_font)
    bw = bbox4[2] - bbox4[0]
    draw.text(((TRAP_W - bw) / 2, TRAP_H - 60), brand, font=brand_font, fill="#555555")

    return normalize_frame(canvas, TRAP_W, TRAP_H)


def trap_intro_card(ctx: TrapRenderContext) -> Image.Image:
    canvas = Image.new("RGB", (TRAP_W, TRAP_H), BG)
    draw = ImageDraw.Draw(canvas)
    title_font = load_font(72, bold=True)
    title = ctx.series_title or "Famous Traps"
    bbox = draw.textbbox((0, 0), title, font=title_font)
    tw = bbox[2] - bbox[0]
    draw.text(((TRAP_W - tw) / 2, TRAP_H / 2 - 80), title, font=title_font, fill=TITLE_YELLOW)

    if ctx.trap_name:
        sub_font = load_font(36)
        sub = fit_text(draw, ctx.trap_name, sub_font, TRAP_W - 100)
        bbox2 = draw.textbbox((0, 0), sub, font=sub_font)
        sw = bbox2[2] - bbox2[0]
        draw.text(((TRAP_W - sw) / 2, TRAP_H / 2 + 20), sub, font=sub_font, fill="#CCCCCC")

    brand_font = load_font(24)
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
