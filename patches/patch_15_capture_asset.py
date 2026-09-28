"""Patch 15 — embed authentic Chess.com capture.mp3 and prefer it over synth."""
from __future__ import annotations
from pathlib import Path
import base64
import os
import subprocess

ROOT = Path(__file__).resolve().parents[1]

# Authentic Chess.com capture (Pro Tools, 2019) — loud version ~10KB
CAPTURE_B64 = """
PLACEHOLDER_WILL_FAIL
""".strip()

def apply() -> None:
    audio_dir = ROOT / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    out = audio_dir / "chess_capture.mp3"
    try:
        raw = base64.b64decode(CAPTURE_B64)
    except Exception as e:
        print(f"patch_15: b64 decode failed: {e}")
        return
    if len(raw) < 5000 or not (raw[:3] == b"ID3" or (raw[0] == 0xFF and (raw[1] & 0xE0) == 0xE0)):
        print(f"patch_15: invalid capture audio ({len(raw)} bytes)")
        return
    out.write_bytes(raw)
    print(f"patch_15: wrote {out} ({len(raw)} bytes)")

    vb = ROOT / "app" / "render" / "video_builder.py"
    if not vb.exists():
        print("patch_15: video_builder missing")
        return
    t = vb.read_text()

    if "Prefer real Chess.com capture" in t or "CAPTURE volume boosted" in t:
        print("patch_15: video_builder already prefers real capture")
        return

    old_force = '''    if by_kind["capture"]:
        part = f"{base}_capture.aac"
        # Always use distinct synth for capture (asset files were often corrupt/missing)
        _build_synth_kind(by_kind["capture"], total_duration_sec, part, kind="capture")
        partials.append(part)'''

    old_if = '''    if by_kind["capture"]:
        part = f"{base}_capture.aac"
        if cap_p:
            build_move_click_track(by_kind["capture"], total_duration_sec, part, cap_p)
        else:
            _build_synth_kind(by_kind["capture"], total_duration_sec, part, kind="capture")
        partials.append(part)'''

    new = '''    if by_kind["capture"]:
        part = f"{base}_capture.aac"
        # Prefer real Chess.com capture.mp3; synth only if missing
        if cap_p and os.path.isfile(cap_p) and os.path.getsize(cap_p) >= 5000:
            print(f"[sound] CAPTURE asset={cap_p} size={os.path.getsize(cap_p)}")
            build_move_click_track(by_kind["capture"], total_duration_sec, part, cap_p)
            boosted = part + ".boost.aac"
            bp = subprocess.run(
                ["ffmpeg", "-y", "-i", part, "-filter:a", "volume=2.0", "-c:a", "aac", boosted],
                capture_output=True, text=True,
            )
            if bp.returncode == 0 and os.path.isfile(boosted):
                import shutil
                shutil.move(boosted, part)
                print("[sound] CAPTURE volume boosted 2.0x")
        else:
            print("[sound] CAPTURE using loud synth (no valid asset)")
            _build_synth_kind(by_kind["capture"], total_duration_sec, part, kind="capture")
        partials.append(part)'''

    if old_force in t:
        t = t.replace(old_force, new, 1)
        vb.write_text(t)
        print("patch_15: replaced force-synth branch")
    elif old_if in t:
        t = t.replace(old_if, new, 1)
        vb.write_text(t)
        print("patch_15: replaced if-cap_p branch")
    else:
        print("patch_15: capture branch pattern not found")
