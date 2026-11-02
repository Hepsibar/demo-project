#!/usr/bin/env bash
# Dev server helper for Git Bash / WSL / Linux.
# Usage: scripts/dev.sh {start|stop|status|restart|logs}

set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/scripts/.dev.pid"
LOG_FILE="$ROOT/scripts/.dev.log"
ERR_FILE="$ROOT/scripts/.dev.err.log"
PORT="${PORT:-8000}"
ACTION="${1:-start}"

running_pid() {
  [ -f "$PID_FILE" ] || return 1
  local p
  p=$(cat "$PID_FILE" 2>/dev/null)
  [ -n "$p" ] && kill -0 "$p" 2>/dev/null && printf '%s' "$p"
}

start_dev() {
  if existing=$(running_pid); then
    echo "already running: PID $existing on http://127.0.0.1:$PORT/"
    return
  fi
  : > "$LOG_FILE"; : > "$ERR_FILE"
  ( cd "$ROOT" && python -m uvicorn main:app --host 127.0.0.1 --port "$PORT" \
      >"$LOG_FILE" 2>"$ERR_FILE" ) &
  echo $! > "$PID_FILE"
  echo "started PID $(cat "$PID_FILE")"
  for _ in $(seq 1 20); do
    sleep 0.5
    if curl -fsS -o /dev/null --max-time 2 "http://127.0.0.1:$PORT/" 2>/dev/null; then
      echo "ready: http://127.0.0.1:$PORT/"
      return
    fi
  done
  echo "WARNING: health check timeout; see $ERR_FILE"
}

stop_dev() {
  if existing=$(running_pid); then
    kill "$existing" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo "stopped PID $existing"
  else
    echo "not running"
  fi
}

status_dev() {
  if existing=$(running_pid); then
    echo "running: PID $existing on http://127.0.0.1:$PORT/"
  else
    echo "not running"
  fi
}

logs_dev() {
  [ -f "$LOG_FILE" ] && { echo "--- stdout ---"; tail -n 40 "$LOG_FILE"; }
  [ -f "$ERR_FILE" ] && { echo "--- stderr ---"; tail -n 40 "$ERR_FILE"; }
}

case "$ACTION" in
  start)   start_dev ;;
  stop)    stop_dev ;;
  restart) stop_dev; start_dev ;;
  status)  status_dev ;;
  logs)    logs_dev ;;
  *) echo "usage: $0 {start|stop|status|restart|logs}"; exit 2 ;;
esac
