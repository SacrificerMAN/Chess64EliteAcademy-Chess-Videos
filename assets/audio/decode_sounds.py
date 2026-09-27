from pathlib import Path
import base64
import shutil
import re

here = Path(__file__).resolve().parent

prefixes = set()
for p in here.glob("*.part*"):
    m = re.match(r"(.+)\.part\d+$", p.name)
    if m:
        prefixes.add(m.group(1))

for prefix in sorted(prefixes):
    parts = sorted(here.glob(f"{prefix}.part*"))
    if not parts:
        continue
    data = "".join(x.read_text().strip() for x in parts)
    b64_path = here / f"{prefix}.mp3.b64"
    b64_path.write_text(data)
    print("assembled", b64_path.name, len(data))

for b64p in list(here.glob("*.mp3.b64")):
    out = here / b64p.name.replace(".b64", "")
    try:
        raw = base64.b64decode(b64p.read_text().strip())
    except Exception as e:
        print("skip bad b64", b64p.name, e)
        continue
    if not (raw[:3] == b"ID3" or (len(raw) > 2 and raw[0] == 0xFF and (raw[1] & 0xE0) == 0xE0)):
        print("reject invalid audio header", out.name)
        if out.exists():
            out.unlink()
        continue
    # Incomplete capture push was ~2.4KB; real file ~6.8KB
    if "capture" in out.name and len(raw) < 5000:
        print("reject incomplete capture", out.name, len(raw))
        if out.exists():
            out.unlink()
        continue
    if len(raw) < 500:
        print("reject too small", out.name, len(raw))
        if out.exists():
            out.unlink()
        continue
    out.write_bytes(raw)
    print("decoded", out.name, len(raw))

mc = here / "move_click.mp3"
if mc.exists():
    alias = here / "chess_move_self.mp3"
    if not alias.exists() or alias.stat().st_size < 100:
        shutil.copy2(mc, alias)
        print("aliased chess_move_self.mp3")

# Drop known-broken partial capture leftovers
for name in ("chess_capture.mp3",):
    f = here / name
    if f.exists() and f.stat().st_size < 5000:
        f.unlink()
        print("removed incomplete", name)
