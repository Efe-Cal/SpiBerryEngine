#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
WORK_DIR="$(dirname "$APP_DIR")"
VENV_PYTHON="$WORK_DIR/venv/bin/python"
APP_MODULE_DIR="$APP_DIR"

SERVICE="sbe.service"

# Stop the service if it's currently running
if systemctl is-active --quiet "$SERVICE" 2>/dev/null; then
    echo "Stopping $SERVICE before running in terminal..."
    sudo systemctl stop "$SERVICE"
fi

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: venv python not found at $VENV_PYTHON" >&2
    exit 1
fi

echo "Starting SpiBerryEngine in terminal..."
PYTHONPATH="$APP_MODULE_DIR" exec "$VENV_PYTHON" -m app.main "$@"
