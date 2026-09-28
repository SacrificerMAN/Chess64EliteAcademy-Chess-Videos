"""Patch 17 — FORCE: non-capture = soft synth only; capture = chess_capture.mp3 only."""
from __future__ import annotations
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VERSION = "capture-only-v17-20260928"


def apply() -> None:
    print(f"[patch_17] {VERSION}")

    # --- 1) Ensure real capture asset exists ---
    audio_dir = ROOT / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    cap = audio_dir / "chess_capture.mp3"
    if not cap.exists() or cap.stat().st_size < 5000:
        urls = [
            "https://raw.githubusercontent.com/Orivoir/scraping-sound-effects-chess.com/main/assets/default/capture.mp3",
            "https://raw.githubusercontent.com/harrenray/Chess-Sounds/main/capture.mp3",
        ]
        for url in urls:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Chess64Elite/1.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = r.read()
                if len(data) >= 5000:
                    cap.write_bytes(data)
                    print(f"[patch_17] downloaded capture {len(data)} bytes")
                    break
            except Exception as e:
                print(f"[patch_17] download fail: {e}")
    else:
        print(f"[patch_17] capture ok {cap.stat().st_size} bytes")

    # --- 2) Force pipeline: move_path=None ---
    pp = ROOT / "app" / "pipeline.py"
    if pp.exists():
        pt = pp.read_text()
        if "move_path=None" in pt and VERSION in pt:
            print("[patch_17] pipeline already forced")
        else:
            new_block = (
                f'    print(f"[sound] VERSION={VERSION} events={{len(sound_events)}}")\n'
                "    build_typed_move_sounds(\n"
                "        sound_events,\n"
                "        total_duration,\n"
                "        click_track_path,\n"
                "        move_path=None,\n"
                "        capture_path=settings.capture_sound_path,\n"
                "        check_path=settings.check_sound_path,\n"
                "    )"
            )
            pat = re.compile(
                r"build_typed_move_sounds\(\s*"
                r"sound_events,\s*"
                r"total_duration,\s*"
                r"click_track_path,\s*"
                r"move_path=[^,]+,\s*"
                r"capture_path=[^,]+,\s*"
                r"check_path=[^)]+\s*"
                r"\)",
                re.MULTILINE,
            )
            if pat.search(pt):
                pt = pat.sub(new_block.strip(), pt, count=1)
                pp.write_text(pt)
                print("[patch_17] pipeline: move_path=None forced")
            else:
                print("[patch_17] pipeline call pattern not found")
                idx = pt.find("build_typed_move_sounds")
                if idx >= 0:
                    print(repr(pt[idx : idx + 280]))

    # --- 3) Config: capture never falls back ---
    cfg = ROOT / "app" / "config.py"
    if cfg.exists():
        t = cfg.read_text()
        bad = 'return self._audio_asset("chess_capture", "capture") or self.move_click_asset_path'
        good = 'return self._audio_asset("chess_capture", "capture")  # never fall back'
        if bad in t:
            cfg.write_text(t.replace(bad, good, 1))
            print("[patch_17] config fallback removed")
        else:
            print("[patch_17] config ok")

    # --- 4) Stamp video_builder ---
    vb = ROOT / "app" / "render" / "video_builder.py"
    if vb.exists():
        t = vb.read_text()
        if VERSION not in t:
            if "def build_typed_move_sounds(" in t:
                t = t.replace(
                    "def build_typed_move_sounds(",
                    f"def build_typed_move_sounds(  # {VERSION}\n",
                    1,
                )
                vb.write_text(t)
                print(f"[patch_17] video_builder stamped {VERSION}")
            else:
                print("[patch_17] build_typed_move_sounds MISSING")
        else:
            print("[patch_17] video_builder already stamped")

    print(f"[patch_17] DONE {VERSION}")
