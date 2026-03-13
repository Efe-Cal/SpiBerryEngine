#!/bin/bash
SERVICE="sbe.service"

ACTIVE=$(systemctl is-active "$SERVICE" 2>/dev/null)
ENABLED=$(systemctl is-enabled "$SERVICE" 2>/dev/null)

echo "===== SpiBerryEngine Status ====="
if [ "$ACTIVE" = "active" ]; then
    echo "  App:     RUNNING"
else
    echo "  App:     NOT RUNNING ($ACTIVE)"
fi

if [ "$ENABLED" = "enabled" ]; then
    echo "  Boot:    ENABLED"
else
    echo "  Boot:    DISABLED"
fi

echo ""
echo "--- Recent logs ---"
journalctl -u "$SERVICE" -n 10 --no-pager
