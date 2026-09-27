#!/usr/bin/env python3
"""Decode bundled chess.com-style sounds from .b64 into .mp3 next to this script."""
import base64
from pathlib import Path
here = Path(__file__).resolve().parent
for b64 in here.glob("*.mp3.b64"):
    out = here / b64.name.replace(".b64", "")
    if out.exists() and out.stat().st_size > 100:
        print("ok", out.name)
        continue
    out.write_bytes(base64.b64decode(b64.read_text().strip()))
    print("wrote", out.name, out.stat().st_size)
