#!/bin/sh
# Optional: only assemble if we have a full set of B* parts
DIR="$(dirname "$0")"
N=$(ls -1 "$DIR"/B* 2>/dev/null | wc -l)
if [ "$N" -lt 5 ]; then
  echo "agent_parts incomplete ($N files), skip assemble — using zip/apply_player_fix"
  exit 0
fi
set -e
cat $(ls -1v "$DIR"/B*) | base64 -d > /app/chess_video_agent_v2.py
echo "assembled agent $(wc -c < /app/chess_video_agent_v2.py) bytes"
