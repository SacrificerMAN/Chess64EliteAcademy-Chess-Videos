#!/bin/sh
set -e
cd /app

# Start Telegram bot in background if token is set
if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -f chess_telegram_bot_v2.py ]; then
  echo "Starting Telegram bot..."
  python3 chess_telegram_bot_v2.py &
  BOT_PID=$!
  echo "Telegram bot PID=$BOT_PID"
else
  echo "TELEGRAM_BOT_TOKEN not set — web only"
fi

# Web UI (foreground — keeps container alive)
PORT="${PORT:-8080}"
echo "Starting web on port $PORT..."
exec uvicorn webapp.app:app --host 0.0.0.0 --port "$PORT"
