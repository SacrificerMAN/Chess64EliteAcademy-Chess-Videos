"""Patch 12 — never crash on corrupt click mp3; fall back to synthetic."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply() -> None:
    p = ROOT / "app" / "render" / "video_builder.py"
    t = p.read_text()
    if "click asset failed" in t:
        print("click fallback already present")
    else:
        old = """    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg click track failed: {proc.stderr[-1500:]}")
    return out_path
"""
        new = """    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        if click_asset_path:
            print(f"click asset failed ({click_asset_path}); using synthetic")
            return build_move_click_track(
                move_timestamps_sec, total_duration_sec, out_path, click_asset_path=None
            )
        raise RuntimeError(f"FFmpeg click track failed: {proc.stderr[-1500:]}")
    return out_path
"""
        if old not in t:
            print("click fail pattern not found")
        else:
            p.write_text(t.replace(old, new, 1))
            print("patched click asset fallback")

    audio = ROOT / "assets" / "audio"
    for name in ("chess_capture.mp3", "chess_capture.mp3.b64"):
        f = audio / name
        if f.exists() and f.stat().st_size < 5000:
            f.unlink()
            print("removed incomplete", name)
