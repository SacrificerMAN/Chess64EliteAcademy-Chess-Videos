#!/bin/sh
set -e
if [ ! -f webapp/app.py ]; then
  echo "webapp/app.py missing, skip wire"
  exit 0
fi
if grep -q 'from fix_resolve import resolve_player_assets' webapp/app.py; then
  echo "already wired"
  exit 0
fi
python3 << 'PY'
from pathlib import Path
p = Path("webapp/app.py")
t = p.read_text()
t = t.replace("resolve_player_assets,", "resolve_player_assets as _old_rpa,", 1)
t = t.replace(
    "from chess_video_agent_v2 import",
    "from fix_resolve import resolve_player_assets\nfrom chess_video_agent_v2 import",
    1,
)
p.write_text(t)
print("wired fix_resolve OK")
PY
