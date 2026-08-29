#!/bin/sh
cd /app

try_write_cred() {
  out="$1"
  label="$2"
  shift 2
  for val in "$@"; do
    [ -z "$val" ] && continue
    first=$(printf '%s' "$val" | head -c 1)
    if [ "$first" = "{" ]; then
      printf '%s' "$val" > "$out"
      echo "OK: wrote $out from $label raw JSON ($(wc -c < "$out") bytes)"
      return 0
    fi
    case "$val" in
      *pehla*|*doosra*|*placeholder*|*xxxx*) continue ;;
    esac
    if printf '%s' "$val" | tr -d '\n\r\t ' | base64 -d > /tmp/cred_try 2>/dev/null; then
      if head -c 1 /tmp/cred_try | grep -q '{'; then
        mv /tmp/cred_try "$out"
        echo "OK: wrote $out from $label base64 ($(wc -c < "$out") bytes)"
        return 0
      fi
    fi
    if [ -f "$val" ]; then
      cp -f "$val" "$out"
      echo "OK: copied $out from path $val"
      return 0
    fi
  done
  return 1
}

echo "=== YouTube credential bootstrap ==="
if try_write_cred /app/client_secrets.json CLIENT_SECRETS \
    "$CLIENT_SECRETS_JSON" \
    "$CLIENT_SECRETS_B64" \
    "$YOUTUBE_CLIENT_SECRETS"
then
  :
else
  echo "FAIL: client_secrets.json not created"
  echo "  Set CLIENT_SECRETS_JSON = full text of client_secrets.json (must start with {)"
fi

if try_write_cred /app/token.json YOUTUBE_TOKEN \
    "$YOUTUBE_TOKEN_JSON" \
    "$YOUTUBE_TOKEN_B64" \
    "$YOUTUBE_TOKEN"
then
  :
else
  echo "FAIL: token.json not created"
  echo "  Set YOUTUBE_TOKEN_JSON = full text of token.json after local OAuth"
fi

export YOUTUBE_CLIENT_SECRETS=/app/client_secrets.json
export YOUTUBE_TOKEN=/app/token.json
ls -la /app/client_secrets.json /app/token.json 2>&1 || true

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
