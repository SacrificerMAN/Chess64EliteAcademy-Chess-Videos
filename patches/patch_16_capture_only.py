"""Patch 16 — capture sound ONLY on real captures; never fall back to move sound."""
from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply() -> None:
    # 1) Config: capture must NOT fall back to move_click
    cfg = ROOT / "app" / "config.py"
    if cfg.exists():
        t = cfg.read_text()
        if "never fall back to move click" in t:
            print("patch_16: config already fixed")
        elif 'return self._audio_asset("chess_capture", "capture") or self.move_click_asset_path' in t:
            t = t.replace(
                'return self._audio_asset("chess_capture", "capture") or self.move_click_asset_path',
                'return self._audio_asset("chess_capture", "capture")  # never fall back to move click',
                1,
            )
            cfg.write_text(t)
            print("patch_16: config capture fallback removed")
        else:
            print("patch_16: config pattern not found")

    # 2) Pipeline: log each sound event kind
    pp = ROOT / "app" / "pipeline.py"
    if pp.exists():
        pt = pp.read_text()
        needle = "sound_events.append((t_cursor, kind))"
        if "[sound] ply=" in pt:
            print("patch_16: pipeline logging already present")
        elif needle in pt:
            pt = pt.replace(
                needle,
                'sound_events.append((t_cursor, kind))\n'
                '        print(f"[sound] ply={i} kind={kind} uci={m.move_uci} t={t_cursor:.2f}")',
                1,
            )
            pp.write_text(pt)
            print("patch_16: pipeline sound event logging added")
        else:
            print("patch_16: pipeline needle not found")

    # 3) video_builder: isolate capture path from move path + log counts
    vb = ROOT / "app" / "render" / "video_builder.py"
    if not vb.exists():
        print("patch_16: video_builder missing")
        return
    t = vb.read_text()
    if "CAPTURE_ONLY_GUARD" in t:
        print("patch_16: typed sounds guard already present")
        return
    if "def build_typed_move_sounds(" not in t:
        print("patch_16: build_typed_move_sounds not present yet")
        return

    anchor = "    chk_p = _ok(check_path)"
    guard = (
        "    chk_p = _ok(check_path)\n"
        "    # CAPTURE_ONLY_GUARD: never let capture asset leak into move track\n"
        "    if move_p and cap_p and os.path.abspath(move_p) == os.path.abspath(cap_p):\n"
        "        print('[sound] WARN: move_path == capture_path; clearing cap_p')\n"
        "        cap_p = None\n"
        "    print(f\"[sound] events move={len(by_kind['move'])} capture={len(by_kind['capture'])} check={len(by_kind['check'])}\")\n"
        "    print(f\"[sound] paths move={move_p} capture={cap_p} check={chk_p}\")"
    )
    if anchor in t:
        t = t.replace(anchor, guard, 1)
        vb.write_text(t)
        print("patch_16: typed sounds path isolation + logging added")
    else:
        print("patch_16: could not inject guard (anchor missing)")
