# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

The WhatsApp Assistant Tool (WA_Tool) is a comprehensive WhatsApp monitoring and automation system with AI integration. It consists of multiple components working together to provide WhatsApp connectivity, AI-powered message processing, and web-based user interfaces.

## Architecture

This is a multi-component system with the following architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WhatsApp      │────│   Go Bridge      │────│   Python MCP    │
│   (Your Phone)  │    │   (Port 8080)    │    │   (Port 3000)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │                         │
                               └─────────┬───────────────┘
                                         │
                               ┌─────────────────┐
                               │  Flask Backend  │
                               │   (Port 5000)   │
                               └─────────────────┘
                                         │
                     ┌───────────────────┴───────────────────┐
                     │                                       │
           ┌─────────────────┐                     ┌─────────────────┐
           │ React Frontend  │                     │ Simple Interface│
           │   (Has Issues)  │                     │   (Port 3001)   │
           └─────────────────┘                     └─────────────────┘
```

### Core Components

1. **WhatsApp Bridge** (`whatsapp-mcp/whatsapp-bridge/`): Go application using whatsmeow library
   - Connects to WhatsApp Web API via QR code authentication
   - Stores messages in SQLite database
   - Provides REST API on port 8080

2. **MCP Server** (`whatsapp-mcp/whatsapp-mcp-server/`): Python MCP implementation
   - Implements Model Context Protocol for AI assistant integration
   - Connects to WhatsApp Bridge via HTTP
   - Runs on port 3000

3. **Flask Backend** (`whatsapp_assistant_app/backend/`): Python Flask API server
   - Provides REST API for web interfaces
   - Integrates with multiple LLM providers (OpenAI, Anthropic, OpenRouter)
   - Runs on port 5000

4. **Web Interfaces**:
   - **React Frontend** (`whatsapp_assistant_app/frontend/`): Material-UI React app (has build issues)
   - **Simple Interface** (`simple_interface/`): Standalone HTML/JS interface on port 3001

## Common Development Commands

### Quick Start/Stop
```bash
# Start all components
./start_wa_tool.sh

# Stop all components  
./stop_wa_tool.sh
```

### Manual Component Management

#### WhatsApp Bridge (Go)
```bash
cd whatsapp-mcp/whatsapp-bridge
mkdir -p store
go run main.go
```

#### MCP Server (Python)
```bash
cd whatsapp-mcp/whatsapp-mcp-server
export PATH="$HOME/.local/bin:$PATH"
uv run main.py
```

#### Flask Backend
```bash
cd whatsapp_assistant_app/backend
source venv/bin/activate
python app.py
```

#### React Frontend (Development)
```bash
cd whatsapp_assistant_app/frontend
npm install
npm start  # Development server
npm run build  # Production build
npm test   # Run tests
```

#### Simple Interface
```bash
cd simple_interface
python3 -m http.server 3001
```

### Docker Deployment
```bash
cd whatsapp_assistant_app
sudo docker-compose up -d    # Start in background
sudo docker-compose down     # Stop and remove
sudo docker-compose logs -f  # View logs
```

### Log Monitoring
```bash
# Individual component logs
tail -f whatsapp-mcp/whatsapp-bridge/whatsapp-bridge.log
tail -f whatsapp-mcp/whatsapp-mcp-server/mcp-server.log  
tail -f whatsapp_assistant_app/backend/flask-backend.log
tail -f simple_interface/frontend.log

# All process activity
ps aux | grep -E "(whatsapp-bridge|main.py|flask.*app.py|http.server)"
```

### Development Testing
```bash
# Check WhatsApp connection status
curl http://localhost:8080/api/status

# Test backend API
curl http://localhost:5000/api/status

# Test message sending
curl -X POST http://localhost:8080/api/send \
  -H "Content-Type: application/json" \
  -d '{"recipient":"PHONE_NUMBER", "message":"Test message"}'
```

## Key Development Areas

### Backend Flask App (`whatsapp_assistant_app/backend/`)
- Main API endpoints: `/api/status`, `/api/send`, `/api/assistant`, `/api/contacts`
- AI integration with multiple LLM providers
- Template system for message formatting
- Message scheduling functionality

### React Frontend Issues (`whatsapp_assistant_app/frontend/`)
- Built with Material-UI and React Router
- Has known build/deployment issues
- Uses proxy to backend on port 5000
- Contains components: App.js, Scheduler.js, Templates.js

### WhatsApp MCP Integration
- Implements full WhatsApp MCP protocol
- Tools available: `mcp4_send_message`, `mcp4_list_chats`, `mcp4_search_contacts`, etc.
- Media handling: send/receive images, videos, audio, documents
- Voice message support with optional ffmpeg integration

### Configuration
Environment variables in `.env`:
- `LLM_API_KEY`: API key for AI providers
- `LLM_PROVIDER`: openrouter|openai|anthropic  
- `LLM_MODEL`: Model identifier (default: x.ai/grok-4-fast:free)
- Port configurations for all components

## Port Allocation
- 8080: WhatsApp Bridge (Go)
- 3000: MCP Server (Python)  
- 5000: Flask Backend
- 3001: Simple Web Interface
- 3000: React development server (when running npm start)

## Database Storage
- WhatsApp messages: `whatsapp-mcp/whatsapp-bridge/store/messages.db`
- WhatsApp sessions: `whatsapp-mcp/whatsapp-bridge/store/whatsapp.db`
- All data stored locally in SQLite

## Authentication & Security
- WhatsApp authentication via QR code scan (re-auth needed ~every 20 days)
- WhatsApp session data stored locally
- No external data transmission except when using AI features
- End-to-end encryption maintained through WhatsApp protocol

## Troubleshooting Common Issues

### WhatsApp Connection
- QR code not appearing: Check bridge logs, restart bridge
- Connection drops: Re-scan QR code, check device limit (max 4)
- Authentication fails: Delete store/*.db files and re-authenticate

### Development Environment
- React frontend build issues: Use simple interface instead
- Port conflicts: Check if components already running with `ps aux | grep`
- UV not found: Ensure `export PATH="$HOME/.local/bin:$PATH"`

### Performance
- Message history loading: Can take minutes for large chat histories
- Database sync issues: Delete and re-authenticate if messages out of sync
- Multiple instances: Only one WhatsApp Bridge can run at a time