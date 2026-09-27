#!/usr/bin/env bash
# Chess64 Elite Academy — Railway entrypoint.
# Runs ordered patches, then supervises two processes:
#   1) FastAPI web (uvicorn)   — Railway health-checks this port
#   2) Telegram bot (polling)  — guarded by a lock file so a redeploy or a
#      second replica can never cause a getUpdates 409 Conflict.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== Chess64 Elite Academy: applying patches =="
python patches/run_patches.py
echo "== decoding move sounds =="
python assets/audio/decode_sounds.py || true

LOCK_FILE="${CHESS64_WORKDIR:-/tmp/chess64_jobs}/bot.lock"
mkdir -p "$(dirname "$LOCK_FILE")"

start_web() {
  echo "== starting web (uvicorn) on port ${PORT:-8080} =="
  exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8080}"
}

start_bot() {
  if [ -e "$LOCK_FILE" ] && kill -0 "$(cat "$LOCK_FILE")" 2>/dev/null; then
    echo "== bot lock held by PID $(cat "$LOCK_FILE"); not starting a second poller =="
    return
  fi
  echo $$ > "$LOCK_FILE"
  trap 'rm -f "$LOCK_FILE"' EXIT
  echo "== starting telegram bot (polling) =="
  python -m app.telegram_bot
}

# --- restart-on-crash supervisor for the bot; web runs in the foreground ---
(
  while true; do
    start_bot || true
    echo "== bot process exited, restarting in 5s =="
    rm -f "$LOCK_FILE"
    sleep 5
  done
) &
BOT_SUPERVISOR_PID=$!

cleanup() {
  echo "== shutting down =="
  kill "$BOT_SUPERVISOR_PID" 2>/dev/null || true
  rm -f "$LOCK_FILE"
}
trap cleanup EXIT INT TERM

start_web
