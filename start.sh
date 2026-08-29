#!/bin/sh
set -e
cd /app

if [ -n "$CLIENT_SECRETS_B64" ]; then
  echo "$CLIENT_SECRETS_B64" | base64 -d > /app/client_secrets.json
  echo "Wrote client_secrets.json from CLIENT_SECRETS_B64"
fi
if [ -n "$YOUTUBE_TOKEN_B64" ]; then
  echo "$YOUTUBE_TOKEN_B64" | base64 -d > /app/token.json
  echo "Wrote token.json from YOUTUBE_TOKEN_B64"
fi

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -f chess_telegram_bot_v2.py ]; then
  echo "Starting Telegram bot..."
  python3 chess_telegram_bot_v2.py &
  echo "Telegram bot PID=$!"
else
  echo "TELEGRAM_BOT_TOKEN not set — web only"
fi

PORT="${PORT:-8080}"
echo "Starting web on port $PORT..."
exec uvicorn webapp.app:app --host 0.0.0.0 --port "$PORT"
