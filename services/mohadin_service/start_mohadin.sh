#!/bin/bash

# Mohadin Service Startup Script
# Starts the Mohadin WhatsApp monitoring service on port 8081

echo "🎯 Starting Mohadin Service..."
echo "Port: 8081"
echo "Mode: Parallel Testing (Safe)"
echo "================================"

cd "$(dirname "$0")"

# Set environment variables
export SERVICE_ID="mohadin"
export SERVICE_PORT="8081"
export CHECK_INTERVAL="15"

# Check if the service is already running
if lsof -i :8081 > /dev/null 2>&1; then
    echo "❌ Port 8081 is already in use"
    echo "   Use 'pkill -f mohadin_service' to stop existing service"
    exit 1
fi

# Start the service
echo "🚀 Launching Mohadin service..."
python3 mohadin_service.py