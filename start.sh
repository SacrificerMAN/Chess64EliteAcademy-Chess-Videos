#!/bin/sh
cd /app

write_json_or_b64() {
  json_val="$1"
  b64_val="$2"
  out="$3"
  label="$4"

  if [ -n "$json_val" ]; then
    printf '%s' "$json_val" > "$out"
    if head -c 1 "$out" | grep -q '{'; then
      echo "OK: wrote $out from ${label}_JSON ($(wc -c < "$out") bytes)"
      return 0
    fi
    echo "WARN: ${label}_JSON does not look like JSON"
    rm -f "$out"
  fi

  if [ -n "$b64_val" ]; then
    case "$b64_val" in
      *pehla*|*doosra*|*xxxx*|*placeholder*)
        echo "WARN: ${label}_B64 is placeholder — skipped"
        return 0
        ;;
    esac
    if echo "$b64_val" | tr -d '\n\r ' | base64 -d > "$out" 2>/dev/null; then
      if head -c 1 "$out" | grep -q '{'; then
        echo "OK: wrote $out from ${label}_B64 ($(wc -c < "$out") bytes)"
        return 0
      fi
      echo "WARN: ${label}_B64 decoded but not JSON"
      rm -f "$out"
    else
      echo "WARN: ${label}_B64 invalid base64 — skipped"
      rm -f "$out"
    fi
  fi
}

write_json_or_b64 "$CLIENT_SECRETS_JSON" "$CLIENT_SECRETS_B64" /app/client_secrets.json CLIENT_SECRETS
write_json_or_b64 "$YOUTUBE_TOKEN_JSON" "$YOUTUBE_TOKEN_B64" /app/token.json YOUTUBE_TOKEN

export YOUTUBE_CLIENT_SECRETS=/app/client_secrets.json
export YOUTUBE_TOKEN=/app/token.json

if [ -f /app/client_secrets.json ]; then
  echo "YouTube client_secrets.json ready"
else
  echo "NOTE: client_secrets.json MISSING — set CLIENT_SECRETS_JSON or CLIENT_SECRETS_B64"
fi
if [ -f /app/token.json ]; then
  echo "YouTube token.json ready"
else
  echo "NOTE: token.json MISSING — set YOUTUBE_TOKEN_JSON or YOUTUBE_TOKEN_B64"
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
