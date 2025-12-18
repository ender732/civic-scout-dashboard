#!/usr/bin/env bash
set -euo pipefail
# Start the civic-scout-agent backend reliably from the repo root
# Usage: ./scripts/start-backend.sh [start|stop|status]

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
AGENT_DIR="$ROOT_DIR/packages/civic-scout-agent"
VENV="$ROOT_DIR/.venv"
PYTHON="$VENV/bin/python"
PIDFILE="$AGENT_DIR/backend.pid"
LOGFILE="$AGENT_DIR/backend.log"
UVCMD="$PYTHON -m uvicorn main:app --host 127.0.0.1 --port 8001 --log-level info"

if [ "$#" -eq 0 ]; then
  cmd=start
else
  cmd="$1"
fi

cd "$AGENT_DIR"

case "$cmd" in
  start)
    if [ ! -x "$PYTHON" ]; then
      echo "Python virtualenv not found at $PYTHON. Create venv and install requirements:"
      echo "  python3 -m venv $VENV && $VENV/bin/pip install -r $AGENT_DIR/requirements.txt"
      exit 1
    fi
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
      echo "Backend already running (PID $(cat $PIDFILE))"
      exit 0
    fi
    nohup $UVCMD > "$LOGFILE" 2>&1 & echo $! > "$PIDFILE"
    echo "Started backend, PID $(cat $PIDFILE), logs: $LOGFILE"
    ;;
  stop)
    if [ -f "$PIDFILE" ]; then
      kill "$(cat $PIDFILE)" && rm -f "$PIDFILE"
      echo "Stopped backend"
    else
      echo "No PID file found; backend may not be running"
    fi
    ;;
  status)
    if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
      echo "Backend running (PID $(cat $PIDFILE))"
    else
      echo "Backend not running"
    fi
    ;;
  *)
    echo "Usage: $0 [start|stop|status]"
    exit 2
    ;;
esac
