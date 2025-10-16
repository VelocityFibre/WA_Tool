#!/bin/bash

# QA Monitor Startup Script
# This script starts the Google Sheets QA Monitor service

# Set working directory
cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server

# Export required environment variables
export PATH="/home/louisdup/.local/bin:$PATH"
export HOME="/home/louisdup"

# Wait a bit for system to be ready (network, etc.)
sleep 30

echo "$(date): Starting QA Monitor Service"

# Use uv to run the monitor with proper environment
exec /home/louisdup/.local/bin/uv run python google_sheets_qa_monitor.py --interval 60
