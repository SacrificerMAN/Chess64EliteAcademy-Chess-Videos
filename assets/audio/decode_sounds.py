from pathlib import Path
import base64
import shutil
here = Path(__file__).resolve().parent
full = here / "move_click.mp3.b64"
if not full.exists() or full.stat().st_size < 4000:
    parts = sorted(here.glob("move_click.part*"))
    if parts:
        data = "".join(p.read_text().strip() for p in parts)
        full.write_text(data)
        print("assembled move_click.mp3.b64", len(data))
for b64p in here.glob("*.mp3.b64"):
    out = here / b64p.name.replace(".b64", "")
    raw = base64.b64decode(b64p.read_text().strip())
    out.write_bytes(raw)
    print("decoded", out.name, len(raw))
src = here / "move_click.mp3"
if src.exists():
    for alias in ("chess_move_self.mp3",):
        dst = here / alias
        if not dst.exists() or dst.stat().st_size < 100:
            shutil.copy2(src, dst)
            print("aliased", alias)
