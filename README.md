# WhatsApp Tool (WA_Tool) Setup Guide

A comprehensive WhatsApp monitoring and automation tool with AI integration.

## 🚀 Quick Start

### Prerequisites
- ✅ Go (installed)
- ✅ Python 3 (installed)
- ✅ Node.js & npm (installed)
- ✅ Docker (installed)
- ✅ UV Python package manager (installed)

### 1. Start the Application

Run the launcher script:
```bash
cd /home/louisdup/VF/Apps/WA_Tool
./start_wa_tool.sh
```

This will start all components:
- **WhatsApp Bridge** (Go) on port 8080
- **MCP Server** (Python) on port 3000  
- **Flask Backend** on port 5000
- **Simple Web Interface** on port 3001

### 2. Connect WhatsApp

1. Look at the terminal output - you'll see a QR code
2. Open WhatsApp on your phone
3. Go to Settings > Linked Devices > Link a Device
4. Scan the QR code displayed in terminal

### 3. Access the Interface

Open your browser and go to:
- **Simple Interface**: http://localhost:3001
- **Backend API**: http://localhost:5000/api/status

### 4. Stop the Application

```bash
./stop_wa_tool.sh
```

## 🏗️ Architecture

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
                               ┌─────────────────┐
                               │  Web Interface  │
                               │   (Port 3001)   │
                               └─────────────────┘
```

## 📁 Directory Structure

```
WA_Tool/
├── whatsapp-mcp/                 # WhatsApp MCP components
│   ├── whatsapp-bridge/          # Go WhatsApp bridge
│   └── whatsapp-mcp-server/      # Python MCP server
├── whatsapp_assistant_app/       # Main application
│   ├── backend/                  # Flask API server
│   └── frontend/                 # React web app (has build issues)
├── simple_interface/             # Simple HTML interface
├── start_wa_tool.sh              # Start all components
├── stop_wa_tool.sh               # Stop all components
├── .env                          # Environment configuration
└── README.md                     # This file
```

## ⚙️ Configuration

Edit `.env` file to configure:

```bash
# LLM Configuration
LLM_API_KEY=your_api_key_here
LLM_PROVIDER=openrouter
LLM_MODEL=x.ai/grok-4-fast:free

# Application Ports
WHATSAPP_BRIDGE_PORT=8080
BACKEND_PORT=5000
FRONTEND_PORT=3001
```

## 🔧 Manual Component Startup

If you prefer to start components individually:

### 1. Start WhatsApp Bridge
```bash
cd whatsapp-mcp/whatsapp-bridge
mkdir -p store
go run main.go
```

### 2. Start MCP Server  
```bash
cd whatsapp-mcp/whatsapp-mcp-server
export PATH="$HOME/.local/bin:$PATH"
uv run main.py
```

### 3. Start Flask Backend
```bash
cd whatsapp_assistant_app/backend
source venv/bin/activate
python app.py
```

### 4. Serve Simple Interface
```bash
cd simple_interface
python3 -m http.server 3001
```

## 📊 Features

### Current Features
- ✅ WhatsApp connection via QR code
- ✅ Real-time message monitoring
- ✅ SQLite message storage
- ✅ REST API for message handling
- ✅ Simple web interface
- ✅ AI-powered message responses
- ✅ Template system
- ✅ Message scheduling

### WhatsApp Capabilities
- Send/receive text messages
- Handle media files (images, videos, documents)
- Group chat support
- Contact management
- Message history

### AI Integration
- Natural language message processing
- Context-aware responses
- Multiple LLM provider support (OpenAI, Anthropic, OpenRouter)
- Custom prompt templates

## 🐛 Troubleshooting

### Common Issues

1. **QR Code not appearing**
   - Check `whatsapp-mcp/whatsapp-bridge/whatsapp-bridge.log`
   - Restart the bridge component

2. **Backend not connecting**
   - Ensure all ports are available (8080, 5000, 3000, 3001)
   - Check `whatsapp_assistant_app/backend/flask-backend.log`

3. **WhatsApp disconnects**
   - Re-scan QR code
   - Check if you have too many linked devices (max 4)

4. **Messages not sending**
   - Verify WhatsApp connection status
   - Check API endpoints are responding

### Log Files

Monitor these log files for debugging:
```bash
# WhatsApp Bridge
tail -f whatsapp-mcp/whatsapp-bridge/whatsapp-bridge.log

# MCP Server
tail -f whatsapp-mcp/whatsapp-mcp-server/mcp-server.log

# Flask Backend  
tail -f whatsapp_assistant_app/backend/flask-backend.log

# Frontend
tail -f simple_interface/frontend.log
```

## 🔒 Security & Privacy

- All WhatsApp data is stored locally in SQLite databases
- No data is sent to external servers except when using AI features
- Messages are encrypted using WhatsApp's end-to-end encryption
- Consider VPN usage for additional privacy

## 📈 Production Deployment

For production use:

1. **Use Docker Compose** (recommended):
   ```bash
   cd whatsapp_assistant_app
   sudo docker-compose up -d
   ```

2. **Set up reverse proxy** (Nginx/Apache)
3. **Configure SSL certificates**
4. **Set up proper logging and monitoring**
5. **Configure automatic restarts**

## 🛠️ Development

To modify the application:

1. **Backend changes**: Edit files in `whatsapp_assistant_app/backend/`
2. **Frontend changes**: Work with React in `whatsapp_assistant_app/frontend/`
3. **Simple interface**: Edit `simple_interface/index.html`

## 📝 API Endpoints

- `GET /api/status` - Check WhatsApp connection
- `GET /api/contacts` - Get contacts list
- `GET /api/chats` - Get chats list  
- `GET /api/messages/{chat_jid}` - Get messages for a chat
- `POST /api/send` - Send a message
- `POST /api/assistant` - Send AI-processed message
- `GET /api/templates` - Get message templates
- `POST /api/schedule` - Schedule a message

## 🤝 Support

For support:
1. Check the logs for error messages
2. Ensure all prerequisites are installed
3. Verify WhatsApp connection via QR code
4. Test individual components manually

---

**Note**: This tool is for monitoring and automation purposes. Please comply with WhatsApp's Terms of Service and local regulations.