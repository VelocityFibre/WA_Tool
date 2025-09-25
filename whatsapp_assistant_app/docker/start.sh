#!/bin/bash

# Start WhatsApp MCP server in the background
cd /app/whatsapp-mcp
npm start &

# Wait for WhatsApp MCP to start
echo "Starting WhatsApp MCP server..."
sleep 5

# Start the backend server
cd /app/backend
echo "Starting backend server..."
python app.py &

# Wait for backend to start
sleep 3

# Serve the frontend
cd /app/frontend/build
echo "Starting frontend server..."
python -m http.server 8080 &

echo "WhatsApp Assistant is running!"
echo "Open your browser and navigate to http://localhost:8080"

# Keep the container running
tail -f /dev/null
