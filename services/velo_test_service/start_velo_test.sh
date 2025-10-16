#!/bin/bash

# Velo Test Service Startup Script
# Starts the Velo Test WhatsApp monitoring service on port 8082

echo "🧪 Starting Velo Test Service..."
echo "Port: 8082"
echo "Mode: Production (Live)"
echo "================================"

cd "$(dirname "$0")"

# Set environment variables
export SERVICE_ID="velo_test"
export SERVICE_PORT="8082"
export CHECK_INTERVAL="15"

# Check if the service is already running
if lsof -i :8082 > /dev/null 2>&1; then
    echo "❌ Port 8082 is already in use"
    echo "   Use 'pkill -f velo_test_service' to stop existing service"
    exit 1
fi

# Start the service
echo "🚀 Launching Velo Test service..."
python3 velo_test_service.py