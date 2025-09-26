#!/bin/bash

# WhatsApp Tool Launcher Script
# This script starts all the necessary components for the WA Tool

# Set colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Export PATH for UV
export PATH="$HOME/.local/bin:$PATH"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   WhatsApp Tool Launcher              ${NC}"
echo -e "${GREEN}========================================${NC}"
echo

# Kill any existing processes
echo -e "${YELLOW}Stopping any existing processes...${NC}"
pkill -f "whatsapp-bridge"
pkill -f "whatsapp-mcp-server"
pkill -f "flask.*app.py"

# Function to start WhatsApp Bridge (Go component)
start_whatsapp_bridge() {
    echo -e "${YELLOW}Starting WhatsApp Bridge...${NC}"
    cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-bridge
    
    # Create store directory
    mkdir -p store
    
    echo "Starting Go WhatsApp bridge on port 8080..."
    echo "You will see a QR code - scan it with your WhatsApp mobile app"
    echo
    
    # Run the bridge in background
    nohup go run main.go > whatsapp-bridge.log 2>&1 &
    BRIDGE_PID=$!
    echo "WhatsApp Bridge started with PID: $BRIDGE_PID"
    
    # Wait a moment for it to initialize
    sleep 5
    
    # Show the log to see QR code
    echo -e "${GREEN}WhatsApp Bridge Log (showing QR code):${NC}"
    timeout 15 tail -f whatsapp-bridge.log &
    
    return $BRIDGE_PID
}

# Function to start WhatsApp MCP Server (Python component)
start_mcp_server() {
    echo -e "${YELLOW}Starting WhatsApp MCP Server...${NC}"
    cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server
    
    echo "Starting Python MCP server on port 3000..."
    
    # Run the MCP server in background
    nohup uv run main.py > mcp-server.log 2>&1 &
    MCP_PID=$!
    echo "WhatsApp MCP Server started with PID: $MCP_PID"
    
    return $MCP_PID
}

# Function to start Flask Backend
start_flask_backend() {
    echo -e "${YELLOW}Starting Flask Backend...${NC}"
    cd /home/louisdup/VF/Apps/WA_Tool/whatsapp_assistant_app/backend
    
    # Set environment variables
    export WHATSAPP_MCP_URL="http://localhost:8080"
    export LLM_API_KEY="${LLM_API_KEY:-}"
    export LLM_MODEL="${LLM_MODEL:-grok-4-fast:free}"
    export LLM_PROVIDER="${LLM_PROVIDER:-openrouter}"
    
    echo "Starting Flask backend on port 5000..."
    
    # Activate venv and run
    source venv/bin/activate
    nohup python app.py > flask-backend.log 2>&1 &
    FLASK_PID=$!
    echo "Flask Backend started with PID: $FLASK_PID"
    
    return $FLASK_PID
}

# Function to serve frontend (simple HTTP server)
start_frontend() {
    echo -e "${YELLOW}Starting Frontend Server...${NC}"
    cd /home/louisdup/VF/Apps/WA_Tool/whatsapp_assistant_app/frontend
    
    # Try to build first, if it fails, serve the src directory
    if [ -d "build" ]; then
        echo "Serving built frontend from build directory..."
        cd build
    else
        echo "Build directory not found, serving development files..."
        # For development, we'll need to run npm start instead
    fi
    
    echo "Starting frontend server on port 3001..."
    nohup python3 -m http.server 3001 > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo "Frontend server started with PID: $FRONTEND_PID"
    
    return $FRONTEND_PID
}

# Start all components
echo -e "${GREEN}Starting all components...${NC}"
echo

# Start WhatsApp Bridge first
start_whatsapp_bridge
BRIDGE_PID=$?

sleep 3

# Start MCP Server
start_mcp_server
MCP_PID=$?

sleep 3

# Start Flask Backend
start_flask_backend
FLASK_PID=$?

sleep 3

# Start Frontend
start_frontend
FRONTEND_PID=$?

echo
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   All components started!              ${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo -e "${YELLOW}Access the application at:${NC}"
echo "  Frontend: http://localhost:3001"
echo "  Backend API: http://localhost:5000"
echo "  WhatsApp Bridge: http://localhost:8080"
echo
echo -e "${YELLOW}Process IDs:${NC}"
echo "  WhatsApp Bridge: $BRIDGE_PID"
echo "  MCP Server: $MCP_PID"
echo "  Flask Backend: $FLASK_PID"
echo "  Frontend: $FRONTEND_PID"
echo
echo -e "${YELLOW}To stop all processes, run:${NC}"
echo "  ./stop_wa_tool.sh"
echo
echo -e "${YELLOW}To view logs:${NC}"
echo "  tail -f whatsapp-mcp/whatsapp-bridge/whatsapp-bridge.log"
echo "  tail -f whatsapp-mcp/whatsapp-mcp-server/mcp-server.log"
echo "  tail -f whatsapp_assistant_app/backend/flask-backend.log"
echo "  tail -f whatsapp_assistant_app/frontend/frontend.log"
echo
echo -e "${GREEN}Setup complete! Don't forget to scan the QR code with WhatsApp.${NC}"