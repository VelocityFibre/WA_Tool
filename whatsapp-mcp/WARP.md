# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a **WhatsApp Model Context Protocol (MCP) Server** with integrated **Quality Assurance Photo Review System** that enables AI assistants like Claude to interact with personal WhatsApp accounts. The system consists of three main components that work together to provide WhatsApp integration for AI assistants and automated quality control for fiber installations.

## Architecture

### Three-Component Architecture
1. **Go WhatsApp Bridge** (`whatsapp-bridge/`): Connects to WhatsApp's web API, handles authentication via QR code, and maintains message history in SQLite
2. **Python MCP Server** (`whatsapp-mcp-server/`): Implements the Model Context Protocol to provide standardized tools for AI assistants
3. **🆕 Real-time Drop Monitor** (`whatsapp-mcp-server/realtime_drop_monitor.py`): Automatically detects drop numbers from WhatsApp messages, creates installation records and QA photo review checklists for quality control workflow

### Data Flow
- AI Assistant (Claude) → Python MCP Server → Go Bridge → WhatsApp API
- WhatsApp → Go Bridge → SQLite Database ← Python MCP Server ← AI Assistant

### Database Structure
- SQLite database stored in `whatsapp-bridge/store/messages.db`
- Tables: `chats` (chat metadata), `messages` (message history with media info)
- Supports media metadata storage including encryption keys and hashes

## Essential Development Commands

### Initial Setup
```bash
# Clone and navigate to project
git clone <repository-url>
cd whatsapp-mcp

# Start the WhatsApp bridge (first-time setup requires QR code scan)
cd whatsapp-bridge
go run main.go

# In separate terminal - run the MCP server
cd whatsapp-mcp-server
uv run main.py
```

### Go Bridge Development
```bash
# Navigate to bridge directory
cd whatsapp-bridge

# Run the bridge (development)
go run main.go

# Build the bridge
go build -o whatsapp-bridge main.go

# Run built binary
./whatsapp-bridge

# Clean and rebuild (useful after dependencies change)
go clean && go build -o whatsapp-bridge main.go
```

### Python MCP Server Development
```bash
# Navigate to server directory
cd whatsapp-mcp-server

# Run with uv (development)
uv run main.py

# Install dependencies
uv sync

# Run specific Python file
uv run python whatsapp.py
```

### 🆕 Quality Control Monitor Development
```bash
# Navigate to server directory
cd whatsapp-mcp-server

# Install systemd service (one-time setup)
./manage_monitor.sh install

# Service management
./manage_monitor.sh start       # Start quality control monitor
./manage_monitor.sh stop        # Stop the monitor
./manage_monitor.sh restart     # Restart the monitor
./manage_monitor.sh status      # Check service status
./manage_monitor.sh logs        # View live monitoring logs

# Development and testing
./manage_monitor.sh test        # Run in test mode (dry-run)

# Manual processing (development)
uv run python realtime_drop_monitor.py --interval 30 --dry-run
```

### 🆕 System Status Monitoring
```bash
# Check overall system health via API
curl http://localhost:3000/api/system-status | jq

# Check individual component status
systemctl status whatsapp-drop-monitor    # Systemd service status
ps aux | grep whatsapp-bridge             # Bridge process status
ps aux | grep "uv run main.py"            # MCP server status

# Monitor database activity
sqlite3 whatsapp-bridge/store/messages.db "SELECT COUNT(*) FROM messages WHERE timestamp > datetime('now', '-1 hour')"

# Check monitor state file
cat whatsapp-mcp-server/monitor_state.json

# Test database connectivity
curl http://localhost:3000/api/installations?limit=1
```

### Windows-Specific Commands
```bash
# Enable CGO for Windows (required for go-sqlite3)
cd whatsapp-bridge
go env -w CGO_ENABLED=1
go run main.go
```

## System Monitoring & Health Checks

### Real-time Status Monitoring
The system includes comprehensive monitoring capabilities through the VF_Drops frontend:

- **System Status API**: `/api/system-status` endpoint provides real-time health checks
- **Automated Monitoring**: Header status indicator updates every 60 seconds
- **Detailed Dashboard**: System Monitor tab with 30-second refresh intervals
- **Component Tracking**: Monitors systemd services and running processes independently

### Monitoring Components

#### 1. Service Detection
- **Systemd Services**: Checks `systemctl is-active` for installed services
- **Process Detection**: Uses `ps aux | grep` to find running processes
- **Hybrid Status**: Components show as active if either systemd OR process is running

#### 2. Database Health
- **WhatsApp SQLite**: Monitors message database activity and recent sync status
- **PostgreSQL**: Tests connectivity to Neon database via API calls
- **Activity Tracking**: Counts messages received in last hour

#### 3. Monitor State Tracking
- **State File**: Reads `monitor_state.json` for last check times
- **Activity Detection**: Considers monitor active if last check within 2 minutes
- **Process Tracking**: Monitors processed message IDs and timestamps

### Status Levels
- **✅ Healthy**: All components operational, databases responsive
- **⚠️ Warning**: Some components down but core functionality working
- **❌ Error**: Critical systems offline or database connectivity issues

### Frontend Integration
- **Header Indicator**: Compact status badge visible on all pages
- **Detailed Dashboard**: Full system breakdown in System Monitor tab
- **Auto-refresh**: No manual intervention needed for status updates
- **Manual Refresh**: Instant status check via "Refresh Now" button

## Key Technical Details

### Authentication Flow
- First run requires QR code scanning with WhatsApp mobile app
- Session persists in `whatsapp-bridge/store/whatsapp.db`
- Re-authentication needed approximately every 20 days
- Device limit: WhatsApp restricts number of linked devices

### Media Handling
- **Storage**: Only metadata stored in database initially
- **Download**: Use `download_media` tool with `message_id` and `chat_jid`
- **Send Files**: Support for images, videos, documents via `send_file`
- **Voice Messages**: `send_audio_message` with automatic Opus conversion (requires FFmpeg)
- **File Locations**: Downloaded media stored in `store/{chat_jid}/` directories

### MCP Tools Available
- `search_contacts`: Find contacts by name/number
- `list_messages`: Retrieve messages with filtering and context
- `list_chats`: Get available chats with metadata
- `send_message`: Send text messages to individuals or groups
- `send_file`: Send media files
- `send_audio_message`: Send voice messages (requires FFmpeg)
- `download_media`: Download and access media files

### Database Schema
- **chats**: `jid`, `name`, `last_message_time`
- **messages**: `id`, `chat_jid`, `sender`, `content`, `timestamp`, `is_from_me`, `media_type`, `filename`, `url`, `media_key`, `file_sha256`, `file_enc_sha256`, `file_length`

## Configuration Files

### Go Module (`whatsapp-bridge/go.mod`)
- Module: `whatsapp-client`
- Go version: 1.24.1
- Key dependencies: whatsmeow (WhatsApp API), go-sqlite3, qrterminal

### Python Project (`whatsapp-mcp-server/pyproject.toml`)
- Project: `whatsapp-mcp-server`
- Python requirement: >=3.11
- Dependencies: httpx, mcp[cli], requests

## Development Environment Setup

### Prerequisites
- Go (1.24+)
- Python 3.11+
- UV (Python package manager)
- FFmpeg (optional, for audio message conversion)
- C compiler (Windows only - MSYS2 recommended)

### Database Reset (Troubleshooting)
```bash
# Remove databases to force re-authentication and sync
rm whatsapp-bridge/store/messages.db
rm whatsapp-bridge/store/whatsapp.db
cd whatsapp-bridge && go run main.go
```

## Troubleshooting Common Issues

### Authentication Problems
- QR code not displaying: Restart bridge application
- Device limit reached: Remove existing devices in WhatsApp → Settings → Linked Devices
- Messages not syncing: Delete database files and re-authenticate

### Windows-Specific Issues
- `CGO_ENABLED=0` error: Enable CGO with `go env -w CGO_ENABLED=1`
- Missing C compiler: Install MSYS2 and add to PATH

### Media Issues
- Audio not playing: Install FFmpeg for automatic Opus conversion
- Media not downloading: Check message_id and chat_jid parameters
- File permissions: Ensure write access to `store/` directory

## File Structure Reference

```
whatsapp-mcp/
├── whatsapp-bridge/           # Go application
│   ├── main.go               # Main bridge application
│   ├── go.mod/go.sum         # Go dependencies
│   └── store/                # SQLite databases and media files
├── whatsapp-mcp-server/      # Python MCP server
│   ├── main.py              # MCP server entry point
│   ├── whatsapp.py          # WhatsApp integration logic
│   ├── audio.py             # Audio processing utilities
│   └── pyproject.toml       # Python project configuration
└── README.md                # Project documentation
```