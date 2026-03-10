#!/bin/bash
echo "Disabling sbe.service (no auto-start on boot)..."
sudo systemctl disable sbe.service
if [ $? -eq 0 ]; then
    echo "sbe.service disabled."
else
    echo "Failed to disable sbe.service." >&2
    exit 1
fi
