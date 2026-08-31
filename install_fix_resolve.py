"""Assemble fix_resolve.py from base64 parts at Docker build."""
from pathlib import Path
import base64
parts = sorted(Path("fix_resolve_parts").glob("P*"))
if not parts:
    print("no fix_resolve_parts")
else:
    data = "".join(p.read_text().strip() for p in parts)
    Path("fix_resolve.py").write_bytes(base64.b64decode(data))
    print("installed fix_resolve.py", Path("fix_resolve.py").stat().st_size)
