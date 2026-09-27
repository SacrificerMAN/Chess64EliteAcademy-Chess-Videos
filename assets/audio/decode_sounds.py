from pathlib import Path
import base64
import shutil
import re

here = Path(__file__).resolve().parent

# Assemble part files: name.part00 + name.part01 + ... -> name.mp3.b64
prefixes = set()
for p in here.glob("*.part*"):
    m = re.match(r"(.+)\.part\d+$", p.name)
    if m:
        prefixes.add(m.group(1))

for prefix in sorted(prefixes):
    parts = sorted(here.glob(f"{prefix}.part*"))
    if not parts:
        continue
    b64_path = here / f"{prefix}.mp3.b64"
    data = "".join(x.read_text().strip() for x in parts)
    b64_path.write_text(data)
    print("assembled", b64_path.name, len(data))

for b64p in here.glob("*.mp3.b64"):
    out = here / b64p.name.replace(".b64", "")
    try:
        raw = base64.b64decode(b64p.read_text().strip())
    except Exception as e:
        print("skip", b64p.name, e)
        continue
    out.write_bytes(raw)
    print("decoded", out.name, len(raw))

mc = here / "move_click.mp3"
if mc.exists():
    alias = here / "chess_move_self.mp3"
    if not alias.exists() or alias.stat().st_size < 100:
        shutil.copy2(mc, alias)
        print("aliased chess_move_self.mp3")
