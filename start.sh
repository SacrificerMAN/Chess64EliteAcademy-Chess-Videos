#!/bin/sh
cd /app

# Optional YouTube OAuth from base64 env (skip if invalid / placeholder)
if [ -n "$CLIENT_SECRETS_B64" ]; then
  if echo "$CLIENT_SECRETS_B64" | base64 -d > /app/client_secrets.json 2>/dev/null; then
    echo "Wrote client_secrets.json from CLIENT_SECRETS_B64"
  else
    echo "WARN: CLIENT_SECRETS_B64 invalid base64 — skipped (YouTube upload needs real credentials)"
    rm -f /app/client_secrets.json
  fi
fi
if [ -n "$YOUTUBE_TOKEN_B64" ]; then
  if echo "$YOUTUBE_TOKEN_B64" | base64 -d > /app/token.json 2>/dev/null; then
    echo "Wrote token.json from YOUTUBE_TOKEN_B64"
  else
    echo "WARN: YOUTUBE_TOKEN_B64 invalid base64 — skipped"
    rm -f /app/token.json
  fi
fi

# Telegram bot (background)
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
