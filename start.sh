#!/bin/sh
cd /app

if [ -n "$BRAND_LOGO_B64" ]; then
  if printf '%s' "$BRAND_LOGO_B64" | tr -d '\n\r\t ' | base64 -d > /app/brand_logo.png 2>/dev/null; then
    echo "OK: brand_logo.png from BRAND_LOGO_B64 ($(wc -c < /app/brand_logo.png) bytes)"
  else
    echo "WARN: BRAND_LOGO_B64 invalid"
    rm -f /app/brand_logo.png
  fi
elif [ -f /app/brand_logo.b64 ] && [ "$(wc -c < /app/brand_logo.b64)" -gt 100 ]; then
  base64 -d < /app/brand_logo.b64 > /app/brand_logo.png 2>/dev/null && echo "OK: brand_logo.png from file" || true
fi

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
fi

if try_write_cred /app/token.json YOUTUBE_TOKEN \
    "$YOUTUBE_TOKEN_JSON" \
    "$YOUTUBE_TOKEN_B64" \
    "$YOUTUBE_TOKEN"
then
  :
else
  echo "FAIL: token.json not created"
fi

export YOUTUBE_CLIENT_SECRETS=/app/client_secrets.json
export YOUTUBE_TOKEN=/app/token.json
ls -la /app/client_secrets.json /app/token.json 2>&1 || true

if [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -f chess_telegram_bot_v2.py ]; then
  echo "Starting Telegram bot (auto-restart, single-instance)..."
  (
    sleep 8
    while true; do
      echo "[bot] launching chess_telegram_bot_v2.py"
      flock -n /tmp/chess64_telegram.lock python3 chess_telegram_bot_v2.py || python3 chess_telegram_bot_v2.py
      code=$?
      echo "[bot] exited code=$code — restart in 8s"
      sleep 8
    done
  ) &
  echo "Telegram bot supervisor PID=$!"
else
  echo "TELEGRAM_BOT_TOKEN not set — web only"
fi

PORT="${PORT:-8080}"
echo "Starting web on port $PORT..."
exec uvicorn webapp.app:app --host 0.0.0.0 --port "$PORT"
