"""
Renders one broadcast-style frame per ply:
  deep navy canvas -> gold-framed board -> last-move highlight -> best-move
  teaching arrow -> top/bottom player bars (photo, flag, name, clock).

Board squares are drawn with cairosvg from python-chess's SVG board (so
piece glyphs are crisp at any size), then composited onto the studio canvas
with Pillow.
"""
from __future__ import annotations

import io
from dataclasses import dataclass

import cairosvg
import chess
import chess.svg
from PIL import Image, ImageDraw

from app.config import settings
from app.player_assets import PlayerAssets
from app.utils import even, fit_text, load_font, normalize_frame

FRAME_W, FRAME_H = 1280, 720  # 16:9, Railway-friendly


@dataclass
class RenderContext:
    theme: str
    white_assets: PlayerAssets
    black_assets: PlayerAssets
    white_name: str
    black_name: str
    clock: str = "10+0"
    show_eval_bar: bool = False


def _board_svg_to_pil(board: chess.Board, size: int, theme: str, last_move: chess.Move | None,
                       arrow: chess.Move | None) -> Image.Image:
    colors = settings.theme_colors(theme)
    fill = {
        "square light": colors["light"],
        "square dark": colors["dark"],
        "square light lastmove": colors["highlight"],
        "square dark lastmove": colors["highlight"],
    }
    arrows = []
    if arrow:
        arrows.append(chess.svg.Arrow(arrow.from_square, arrow.to_square, color="#00b3ff"))
    svg_data = chess.svg.board(
        board,
        size=size,
        lastmove=last_move,
        colors=fill,
        arrows=arrows,
    )
    png_bytes = cairosvg.svg2png(bytestring=svg_data.encode("utf-8"), output_width=size, output_height=size)
    return Image.open(io.BytesIO(png_bytes)).convert("RGBA")


def _draw_player_bar(canvas: Image.Image, assets: PlayerAssets, name: str, y: int, height: int,
                      flag_code: str | None, clock: str) -> None:
    draw = ImageDraw.Draw(canvas)
    w = canvas.width
    draw.rectangle((0, y, w, y + height), fill="#0e1830")
    draw.line((0, y, w, y), fill=settings.GOLD, width=2)

    # circular photo
    avatar_d = height - 16
    avatar = assets.avatar_image.resize((avatar_d, avatar_d)).convert("RGBA")
    mask = Image.new("L", (avatar_d, avatar_d), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avatar_d, avatar_d), fill=255)
    canvas.paste(avatar, (16, y + 8), mask)
    ring_box = (14, y + 6, 14 + avatar_d + 4, y + 6 + avatar_d + 4)
    draw.ellipse(ring_box, outline=settings.GOLD, width=3)

    # name + flag
    font = load_font(28, bold=True)
    label = name if not flag_code else f"{name}  [{flag_code.upper()}]"
    label = fit_text(draw, label, font, w - avatar_d - 220)
    draw.text((16 + avatar_d + 16, y + height / 2 - 18), label, font=font, fill="#f2e6c9")

    # clock
    clock_font = load_font(24, bold=True)
    draw.text((w - 120, y + height / 2 - 14), clock, font=clock_font, fill=settings.GOLD)


def render_frame(
    ctx: RenderContext,
    board: chess.Board,
    last_move: chess.Move | None,
    best_move: chess.Move | None,
    eval_cp: float | None,
) -> Image.Image:
    canvas = Image.new("RGB", (FRAME_W, FRAME_H), settings.NAVY_BG)
    bar_h = 96
    board_area_h = FRAME_H - 2 * bar_h
    board_px = even(min(settings.board_size, board_area_h - 24, FRAME_W - 24))

    board_img = _board_svg_to_pil(board, board_px, ctx.theme, last_move, best_move)

    # gold frame around the board
    frame_pad = 6
    framed = Image.new("RGBA", (board_px + frame_pad * 2, board_px + frame_pad * 2), settings.GOLD)
    framed.paste(board_img, (frame_pad, frame_pad))

    canvas_rgba = canvas.convert("RGBA")
    bx = (FRAME_W - framed.width) // 2
    by = bar_h + (board_area_h - framed.height) // 2
    canvas_rgba.paste(framed, (bx, by))
    canvas = canvas_rgba.convert("RGB")

    # top bar = Black, bottom bar = White (per spec)
    _draw_player_bar(canvas, ctx.black_assets, ctx.black_name, 0, bar_h, ctx.black_assets.country_code, ctx.clock)
    _draw_player_bar(
        canvas, ctx.white_assets, ctx.white_name, FRAME_H - bar_h, bar_h, ctx.white_assets.country_code, ctx.clock
    )

    if ctx.show_eval_bar and eval_cp is not None:
        _draw_eval_bar(canvas, eval_cp, bar_h, FRAME_H - bar_h)

    return normalize_frame(canvas, FRAME_W, FRAME_H)


def _draw_eval_bar(canvas: Image.Image, eval_cp: float, top: int, bottom: int) -> None:
    draw = ImageDraw.Draw(canvas)
    bar_w = 14
    x = canvas.width - bar_w - 6
    height = bottom - top
    # clamp to +-1000cp for the bar fill
    clamped = max(-1000.0, min(1000.0, eval_cp))
    white_frac = 0.5 + (clamped / 2000.0)
    white_h = int(height * white_frac)
    draw.rectangle((x, top, x + bar_w, bottom), fill="#333333")
    draw.rectangle((x, bottom - white_h, x + bar_w, bottom), fill="#eeeeee")


def intro_card(ctx: RenderContext, title_line: str, brand_hashtag: str) -> Image.Image:
    """A short branded intro frame (held for ~1.5s at the start of the video)."""
    canvas = Image.new("RGB", (FRAME_W, FRAME_H), settings.NAVY_BG)
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, FRAME_W, FRAME_H), outline=settings.GOLD, width=8)

    title_font = load_font(56, bold=True)
    sub_font = load_font(30)
    line = fit_text(draw, title_line, title_font, FRAME_W - 160)
    bbox = draw.textbbox((0, 0), line, font=title_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((FRAME_W - tw) / 2, FRAME_H / 2 - th), line, font=title_font, fill="#f2e6c9")

    vs_line = f"{ctx.white_name}  vs  {ctx.black_name}"
    bbox2 = draw.textbbox((0, 0), vs_line, font=sub_font)
    tw2 = bbox2[2] - bbox2[0]
    draw.text(((FRAME_W - tw2) / 2, FRAME_H / 2 + th), vs_line, font=sub_font, fill=settings.GOLD)

    brand_font = load_font(22)
    draw.text((24, FRAME_H - 44), brand_hashtag, font=brand_font, fill=settings.GOLD)
    return normalize_frame(canvas, FRAME_W, FRAME_H)
