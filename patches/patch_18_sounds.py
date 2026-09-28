"""Patch 18 — definitive Chess.com sounds: distinct move / capture / check."""
from __future__ import annotations
from pathlib import Path
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


def _force_download(name: str, audio_dir: Path) -> None:
    """Always re-download so stale/corrupt files cannot stick around."""
    out = audio_dir / name
    for url in _URLS.get(name, []):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Chess64Elite/1.0"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = r.read()
            if _write_mp3(out, data):
                print(f"[patch_18] FORCE wrote {out.name} ({len(data)} bytes) from {url}")
                return
            print(f"[patch_18] bad data from {url} size={len(data)}")
        except Exception as e:
            print(f"[patch_18] dl fail {url}: {e}")
    if out.exists() and out.stat().st_size >= 500:
        print(f"[patch_18] keep existing {out.name} ({out.stat().st_size} bytes) — download failed")
    else:
        print(f"[patch_18] FAILED {name}")


def apply() -> None:
    print(f"[patch_18] {VERSION}")
    audio_dir = ROOT / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Always overwrite — do not trust leftover files from previous deploys
    for name in ("chess_capture.mp3", "chess_move_self.mp3", "chess_move_check.mp3"):
        _force_download(name, audio_dir)

    mc = audio_dir / "move_click.mp3"
    src = audio_dir / "chess_move_self.mp3"
    if src.exists():
        mc.write_bytes(src.read_bytes())
        print(f"[patch_18] aliased move_click.mp3 ({mc.stat().st_size} bytes)")

    print(f"[patch_18] DONE {VERSION}")
    # List what we have so logs prove it
    for p in sorted(audio_dir.glob("*.mp3")):
        print(f"[patch_18] asset {p.name} = {p.stat().st_size} bytes")
