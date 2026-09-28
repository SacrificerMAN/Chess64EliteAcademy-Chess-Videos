"""Patch 18 — definitive Chess.com sounds: distinct move / capture / check."""
from __future__ import annotations
from pathlib import Path
import base64
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VERSION = "sounds-v18-20260928"

_URLS = {
    "chess_capture.mp3": [
        "https://raw.githubusercontent.com/Orivoir/scraping-sound-effects-chess.com/main/assets/default/capture.mp3",
        "https://raw.githubusercontent.com/harrenray/Chess-Sounds/main/capture.mp3",
    ],
    "chess_move_self.mp3": [
        "https://raw.githubusercontent.com/Orivoir/scraping-sound-effects-chess.com/main/assets/default/move-self.mp3",
    ],
    "chess_move_check.mp3": [
        "https://raw.githubusercontent.com/Orivoir/scraping-sound-effects-chess.com/main/assets/default/move-check.mp3",
    ],
}


def _write_mp3(path: Path, data: bytes) -> bool:
    if len(data) < 500:
        return False
    if not (data[:3] == b"ID3" or (data[0] == 0xFF and (data[1] & 0xE0) == 0xE0)):
        return False
    path.write_bytes(data)
    return True


def _ensure(name: str, audio_dir: Path) -> None:
    out = audio_dir / name
    min_size = 5000 if "capture" in name else 500
    if out.exists() and out.stat().st_size >= min_size:
        print(f"[patch_18] keep {out.name} ({out.stat().st_size} bytes)")
        return
    b64p = audio_dir / f"{name}.b64"
    if b64p.exists():
        try:
            data = base64.b64decode(b64p.read_text().strip())
            if _write_mp3(out, data):
                print(f"[patch_18] from b64 {out.name} ({len(data)} bytes)")
                return
        except Exception as e:
            print(f"[patch_18] b64 fail {name}: {e}")
    for url in _URLS.get(name, []):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Chess64Elite/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            if _write_mp3(out, data):
                print(f"[patch_18] downloaded {out.name} ({len(data)} bytes)")
                return
        except Exception as e:
            print(f"[patch_18] dl fail {url}: {e}")
    print(f"[patch_18] FAILED {name}")


def apply() -> None:
    print(f"[patch_18] {VERSION}")
    audio_dir = ROOT / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    for name in ("chess_capture.mp3", "chess_move_self.mp3", "chess_move_check.mp3"):
        _ensure(name, audio_dir)

    mc = audio_dir / "move_click.mp3"
    src = audio_dir / "chess_move_self.mp3"
    if src.exists() and (not mc.exists() or mc.stat().st_size < 500):
        mc.write_bytes(src.read_bytes())
        print("[patch_18] aliased move_click.mp3")

    pp = ROOT / "app" / "pipeline.py"
    if pp.exists():
        pt = pp.read_text()
        old_kind = (
            "        if is_check:\n"
            "            kind = \"check\"\n"
            "        elif is_capture:\n"
            "            kind = \"capture\"\n"
            "        else:\n"
            "            kind = \"move\""
        )
        new_kind = (
            "        if is_capture:\n"
            "            kind = \"capture\"\n"
            "        elif is_check:\n"
            "            kind = \"check\"\n"
            "        else:\n"
            "            kind = \"move\""
        )
        if old_kind in pt:
            pt = pt.replace(old_kind, new_kind, 1)
            print("[patch_18] capture priority over check")
        if "move_path=None" in pt:
            pt = pt.replace("move_path=None", "move_path=settings.move_click_asset_path", 1)
            print("[patch_18] restored move_path")
        if VERSION not in pt:
            if "VERSION=capture-only-v17" in pt:
                pt = pt.replace("VERSION=capture-only-v17-20260928", f"VERSION={VERSION}", 1)
            print("[patch_18] version stamp")
        pp.write_text(pt)

    cfg = ROOT / "app" / "config.py"
    if cfg.exists():
        t = cfg.read_text()
        bad = 'return self._audio_asset("chess_capture", "capture") or self.move_click_asset_path'
        if bad in t:
            cfg.write_text(t.replace(bad, 'return self._audio_asset("chess_capture", "capture")', 1))
            print("[patch_18] config fixed")
    print(f"[patch_18] DONE {VERSION}")
