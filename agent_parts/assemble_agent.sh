#!/bin/sh
set -e
DIR="$(dirname "$0")"
cat $(ls -1v "$DIR"/B*) | base64 -d > /app/chess_video_agent_v2.py
echo "assembled agent $(wc -c < /app/chess_video_agent_v2.py) bytes"
grep -q 'so, wesley' /app/chess_video_agent_v2.py && echo "OK: so, wesley present"
grep -q 'force = used_user' /app/chess_video_agent_v2.py && echo "OK: force refresh present"
