#!/bin/bash
echo "Starting sbe.service..."
sudo systemctl start sbe.service
if [ $? -eq 0 ]; then
    echo "sbe.service started successfully."
else
    echo "Failed to start sbe.service." >&2
    exit 1
fi
