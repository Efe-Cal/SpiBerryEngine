#!/bin/bash
echo "Enabling sbe.service (auto-start on boot)..."
sudo systemctl enable sbe.service
if [ $? -eq 0 ]; then
    echo "sbe.service enabled."
else
    echo "Failed to enable sbe.service." >&2
    exit 1
fi
