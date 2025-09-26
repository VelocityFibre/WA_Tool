#!/bin/bash

# WhatsApp Tool Stop Script
# This script stops all the running components

# Set colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}========================================${NC}"
echo -e "${RED}   Stopping WhatsApp Tool               ${NC}"
echo -e "${RED}========================================${NC}"
echo

echo -e "${YELLOW}Stopping all WA Tool processes...${NC}"

# Kill processes by name
pkill -f "whatsapp-bridge" && echo "✓ Stopped WhatsApp Bridge"
pkill -f "whatsapp-mcp-server" && echo "✓ Stopped WhatsApp MCP Server"
pkill -f "main.py" && echo "✓ Stopped MCP Server Python processes"
pkill -f "flask.*app.py" && echo "✓ Stopped Flask Backend"
pkill -f "http.server 3001" && echo "✓ Stopped Frontend Server"
pkill -f "go run main.go" && echo "✓ Stopped Go processes"

# Also kill by port (backup method)
fuser -k 8080/tcp 2>/dev/null && echo "✓ Killed processes on port 8080"
fuser -k 5000/tcp 2>/dev/null && echo "✓ Killed processes on port 5000"
fuser -k 3001/tcp 2>/dev/null && echo "✓ Killed processes on port 3001"
fuser -k 3000/tcp 2>/dev/null && echo "✓ Killed processes on port 3000"

echo
echo -e "${GREEN}All WA Tool processes stopped.${NC}"
echo
echo -e "${YELLOW}Logs are preserved:${NC}"
echo "  whatsapp-mcp/whatsapp-bridge/whatsapp-bridge.log"
echo "  whatsapp-mcp/whatsapp-mcp-server/mcp-server.log"
echo "  whatsapp_assistant_app/backend/flask-backend.log"
echo "  whatsapp_assistant_app/frontend/frontend.log"