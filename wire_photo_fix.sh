#!/bin/sh
set -e
python3 expand_known.py 2>/dev/null || true

if [ -f webapp/app.py ]; then
  if ! grep -q 'from fix_resolve import resolve_player_assets' webapp/app.py; then
    python3 << 'PY'
from pathlib import Path
p = Path("webapp/app.py")
t = p.read_text()
t = t.replace("resolve_player_assets,", "resolve_player_assets as _old_rpa,", 1)
t = t.replace(
    "from chess_video_agent_v2 import",
    "from fix_resolve import resolve_player_assets\nfrom recent_games import list_recent_decisive\nfrom chess_video_agent_v2 import",
    1,
)
p.write_text(t)
print("wired fix_resolve + recent_games")
PY
  else
    if ! grep -q 'list_recent_decisive' webapp/app.py; then
      sed -i 's/from fix_resolve import resolve_player_assets/from fix_resolve import resolve_player_assets\nfrom recent_games import list_recent_decisive/' webapp/app.py || true
      echo "added recent_games import"
    fi
  fi

  if ! grep -q '/api/recent-games' webapp/app.py; then
    python3 << 'PY'
from pathlib import Path
p = Path("webapp/app.py")
t = p.read_text()
endpoint = '''

@app.get("/api/recent-games")
async def api_recent_games(player: str = "", source: str = "chesscom", limit: int = 10):
    player = (player or "").strip()
    if not player:
        raise HTTPException(400, "player required")
    limit = max(1, min(int(limit or 10), 15))
    source = (source or "chesscom").lower()
    prefer_otb = source in ("tournament", "fide", "otb")
    try:
        games = await asyncio.to_thread(list_recent_decisive, player, source, limit, prefer_otb)
    except Exception as e:
        raise HTTPException(500, f"fetch failed: {e}")
    out = [{k: g.get(k) for k in ("white","black","result","event","time_class","url","is_otb","end_time","pgn")} for g in games]
    return {"player": player, "source": source, "count": len(out), "games": out}
'''
    if '@app.get("/api/health")' in t:
        t = t.replace('@app.get("/api/health")', endpoint + '\n@app.get("/api/health")', 1)
    else:
        t += endpoint
    p.write_text(t)
    print("injected /api/recent-games")
  fi
fi

if [ -f webapp/static/index_new.html ]; then
  cp -f webapp/static/index_new.html webapp/static/index.html
  echo "applied index_new.html UI"
fi
