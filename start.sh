#!/bin/sh
cd /app

write_b64() {
  val="$1"
  out="$2"
  label="$3"
  if [ -z "$val" ]; then
    return 0
  fi
  case "$val" in
    *base64*|*pehla*|*doosra*|*xxxx*)
      echo "WARN: $label looks like placeholder — skipped"
      return 0
      ;;
  esac
  if echo "$val" | base64 -d > "$out" 2>/dev/null; then
    if head -c 1 "$out" | grep -q '{'; then
      echo "OK: wrote $out from $label ($(wc -c < "$out") bytes)"
    else
      echo "WARN: $label decoded but not JSON — removed"
      rm -f "$out"
    fi
  else
    echo "WARN: $label invalid base64 — skipped"
    rm -f "$out"
  fi
}

write_b64 "$CLIENT_SECRETS_B64" /app/client_secrets.json CLIENT_SECRETS_B64
write_b64 "$YOUTUBE_TOKEN_B64" /app/token.json YOUTUBE_TOKEN_B64

export YOUTUBE_CLIENT_SECRETS=/app/client_secrets.json
export YOUTUBE_TOKEN=/app/token.json

if [ -f /app/client_secrets.json ]; then
  echo "YouTube client_secrets.json ready"
else
  echo "NOTE: no client_secrets.json — set CLIENT_SECRETS_B64 to base64 of the OAuth JSON file"
fi
if [ -f /app/token.json ]; then
  echo "YouTube token.json ready"
else
  echo "NOTE: no token.json — OAuth once locally, then set YOUTUBE_TOKEN_B64"
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
