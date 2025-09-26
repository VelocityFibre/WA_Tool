# AI Agent Guide - WA_Tool Directory

## 🤖 **For AI Agents: What is this directory?**

This directory contains the **WhatsApp Assistant Tool (WA_Tool)** - a comprehensive WhatsApp monitoring and automation system specifically designed for tracking designated project groups for VelocityFibre's infrastructure projects.

## 🎯 **Primary Purpose**

- **Project-Based WhatsApp Group Tracking**: Monitors specific WhatsApp groups for Lawley and Velo Test projects
- **Real-time Drop Number Detection**: Automatically extracts and syncs DR numbers to Neon database
- **Quality Control Integration**: Creates QA photo review entries for detected installations
- **API-Driven Architecture**: Provides REST APIs for frontend applications

## 📋 **Current Version: 2.0.0**

### **Active Projects Being Monitored:**
| Project | WhatsApp Group JID | Description |
|---------|-------------------|-------------|
| **Lawley** | `120363418298130331@g.us` | Lawley Activation 3 group |
| **Velo Test** | `120363421664266245@g.us` | Velo Test group |

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WhatsApp      │────│   Go Bridge      │────│   Python MCP    │
│   (Phone App)   │    │   (Port 8080)    │    │   (Port 3000)   │
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
           │   Web Frontend  │                     │  Real-time      │
           │   (Port 3001)   │                     │  Drop Monitor   │
           └─────────────────┘                     └─────────────────┘
                                                           │
                                                 ┌─────────────────┐
                                                 │  Neon Database  │
                                                 │  (PostgreSQL)   │
                                                 └─────────────────┘
```

## 📁 **Directory Structure for AI Agents**

```
/home/louisdup/VF/Apps/WA_Tool/
├── whatsapp-mcp/                          # Core WhatsApp integration
│   ├── whatsapp-bridge/                   # Go service (Port 8080)
│   │   ├── main.go                        # WhatsApp connection & project filtering
│   │   └── store/messages.db              # SQLite database (project chats only)
│   └── whatsapp-mcp-server/              # Python MCP service (Port 3000)
│       ├── main.py                        # MCP server implementation
│       ├── realtime_drop_monitor.py       # Real-time DR number detection
│       └── sync_drops_to_neon.py          # Manual Neon DB sync tool
├── whatsapp_assistant_app/               # Web application layer
│   ├── backend/                          # Flask API server (Port 5000)
│   │   ├── app.py                        # Project-specific REST APIs
│   │   ├── scheduler.py                  # Message scheduling
│   │   └── templates.py                  # Message templates
│   └── frontend/                         # React app (has build issues)
├── simple_interface/                     # Working HTML interface (Port 3001)
├── start_wa_tool.sh                      # Service startup script
├── stop_wa_tool.sh                       # Service shutdown script
├── migrate_project_names.py              # Database migration tool
├── PROJECT_API_ENDPOINTS.md              # API documentation for frontend
├── CHANGELOG.md                          # Version history
├── README.md                             # User setup guide
└── AI_AGENT_GUIDE.md                     # This file
```

## 🔌 **Service Ports & Status**

| Service | Port | Status | Purpose |
|---------|------|--------|---------|
| **WhatsApp Bridge (Go)** | 8080 | ✅ Running | WhatsApp connectivity & message storage |
| **MCP Server (Python)** | 3000 | ✅ Running | WhatsApp MCP protocol implementation |
| **Flask Backend** | 5000 | ✅ Running | REST APIs for frontend applications |
| **Simple Interface** | 3001 | Available | Basic web interface |
| **Real-time Monitor** | - | ✅ Active | Systemd service (15s intervals) |

## 🗄️ **Database Architecture**

### **SQLite (Local Storage)**
- **Location**: `whatsapp-mcp/whatsapp-bridge/store/messages.db`
- **Purpose**: WhatsApp chats and messages for tracked projects only
- **Schema**: 
  - `chats` table with `project_name` column
  - `messages` table with media support
- **Data**: Only Lawley and Velo Test group data (individual contacts excluded)

### **Neon PostgreSQL (Cloud)**
- **Purpose**: Installation tracking and QA management
- **Tables**:
  - `installations` - Drop numbers with `project_name` column
  - `qa_photo_reviews` - QA tracking with `project_name` column
- **Integration**: Auto-synced by real-time monitor

## 🔄 **Key Processes**

### **Real-time Drop Number Detection**
1. **Monitor**: Watches both project WhatsApp groups every 15 seconds
2. **Extract**: Finds DR numbers using regex pattern `DR\d+`
3. **Validate**: Checks against existing Neon database records  
4. **Sync**: Creates installation and QA review records
5. **Log**: Comprehensive logging for debugging

### **Project-Specific APIs**
- `GET /api/projects` - List tracked projects
- `GET /api/chats/<project_name>` - Project-filtered chats
- `GET /api/messages/<project_name>/<chat_jid>` - Project messages with validation

## 🧠 **AI Agent Context Rules**

### **When Working with This Directory:**

1. **Project Scope**: Only work with Lawley and Velo Test groups
2. **Database**: SQLite for WhatsApp data, Neon for business data
3. **Services**: All 4 core services should be running for full functionality
4. **Security**: WhatsApp data stays local, only DR numbers go to cloud
5. **Monitoring**: Real-time drop detection is business-critical

### **Common Tasks:**
- **Service Management**: Use `start_wa_tool.sh` and `stop_wa_tool.sh`
- **Database Queries**: Direct SQLite access for WhatsApp data analysis
- **API Testing**: Use curl against localhost ports for verification
- **Log Analysis**: Check service logs in respective directories

### **Important Files to Preserve:**
- `whatsapp-bridge/store/` - Contains WhatsApp session and message data
- `backend/venv/` - Python virtual environment
- `*.log` files - Service execution logs
- `.env` - Environment configuration (if exists)

## 🔧 **Configuration Files**

- **Environment**: `.env` file for API keys and settings
- **SSH**: `~/.ssh/config` with GitHub repository access
- **Systemd**: Real-time monitor runs as system service
- **Project Config**: Embedded in Go and Python code (PROJECTS map)

## 📊 **Monitoring & Health Checks**

### **Service Health:**
```bash
# Check all services
ps aux | grep -E "(whatsapp-bridge|main.py|app.py|http.server)"

# Test APIs
curl http://localhost:8080/api/status  # WhatsApp Bridge
curl http://localhost:3000/           # MCP Server  
curl http://localhost:5000/api/status # Flask Backend
curl http://localhost:3001/           # Simple Interface
```

### **Database Status:**
```bash
# SQLite project data
sqlite3 whatsapp-mcp/whatsapp-bridge/store/messages.db "SELECT project_name, COUNT(*) FROM chats GROUP BY project_name;"

# Real-time monitor status
sudo systemctl status whatsapp-drop-monitor
```

## 🚨 **Critical Success Factors**

1. **WhatsApp Connection**: Must maintain QR code authentication
2. **Project Groups**: Only monitor designated groups (no individual contacts)
3. **Real-time Sync**: Drop number detection must be continuously operational
4. **Database Integrity**: SQLite and Neon must stay synchronized
5. **API Availability**: Frontend depends on all REST endpoints

## 🎯 **Current State (as of v2.0.0)**

- ✅ All services operational and tested
- ✅ Project filtering implemented and verified  
- ✅ Real-time monitoring active (15-second intervals)
- ✅ APIs documented and ready for frontend integration
- ✅ Database schema updated with project tracking
- ✅ Comprehensive documentation complete

**This directory is production-ready for project-based WhatsApp group monitoring and drop number tracking.**