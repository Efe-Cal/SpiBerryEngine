#!/bin/bash
echo "Stopping sbe.service..."
sudo systemctl stop sbe.service
if [ $? -eq 0 ]; then
    echo "sbe.service stopped successfully."
else
    echo "Failed to stop sbe.service." >&2
    exit 1
fi
