# WA_Tool Changelog

## [2.0.0] - 2025-09-26

### 🚀 Major Features Added

#### Project-Based WhatsApp Group Tracking
- **NEW**: Added support for tracking specific WhatsApp project groups only
- **BREAKING**: System now only monitors designated project groups, ignoring individual contacts
- **Projects**: Currently tracking Lawley and Velo Test groups

#### Database Schema Enhancements
- **Added**: `project_name` column to `chats` table in SQLite database
- **Migration**: Automatic project assignment based on WhatsApp group JIDs
- **Cleanup**: Removed all individual contact records (162 contacts) - only project groups remain

#### New API Endpoints
- `GET /api/projects` - List all tracked projects with chat counts
- `GET /api/chats/<project_name>` - Get chats filtered by project
- `GET /api/messages/<project_name>/<chat_jid>` - Get project-specific messages with validation

#### Updated Components

##### WhatsApp Bridge (Go)
- **Updated**: Automatic project name assignment for new chats
- **Filter**: Only stores chats from designated project groups
- **Projects**: Embedded project configuration with JID mapping

##### Flask Backend
- **Fixed**: Database path resolution issue
- **Added**: Project-specific API endpoints with proper filtering
- **Enhanced**: Error handling for project/chat validation

##### Neon Database Integration
- **Confirmed**: Both Lawley and Velo Test projects supported
- **Tables**: `installations` and `qa_photo_reviews` with `project_name` columns
- **Monitoring**: Real-time drop number detection for both projects

### 📋 Current Project Configuration

| Project | WhatsApp Group JID | Description |
|---------|-------------------|-------------|
| Lawley | `120363418298130331@g.us` | Lawley Activation 3 group |
| Velo Test | `120363421664266245@g.us` | Velo Test group |

### 🔧 Technical Changes

#### Files Modified
- `whatsapp-mcp/whatsapp-bridge/main.go` - Added project configurations and filtering
- `whatsapp_assistant_app/backend/app.py` - Fixed DB path and added project APIs
- Database schema: Added `project_name` column to `chats` table

#### Files Added
- `PROJECT_API_ENDPOINTS.md` - Complete API documentation for frontend integration
- `migrate_project_names.py` - Database migration script for project classification

#### Services Status
- ✅ WhatsApp Bridge (Go) - Port 8080
- ✅ MCP Server (Python) - Port 3000  
- ✅ Real-time Drop Monitor - Systemd service (15s intervals)
- ✅ Flask Backend - Port 5000

### 🎯 Frontend Integration Ready

The system now provides:
- Project selection capability (Lawley vs Velo Test)
- Separate drop number tracking per project
- Project-filtered QA photo reviews
- Project-specific chat and message APIs

### 🔄 Migration Impact

- **Before**: 164 total chats (162 individual + 2 groups)
- **After**: 2 project chats only (Lawley + Velo Test)
- **Data**: Individual contact chat history preserved but not accessible via new APIs
- **Monitoring**: Real-time drop detection continues for both project groups

### 📚 Documentation

- Complete API documentation available in `PROJECT_API_ENDPOINTS.md`
- React integration examples provided
- Error handling patterns documented
- Testing commands included

### ⚠️ Breaking Changes

- Individual contacts no longer tracked in system
- Old `/api/chats` endpoint now only returns project groups
- Database path fixed - may require service restart
- Project-specific validation added to message endpoints

### 🧪 Tested & Verified

- All API endpoints tested and working
- Database queries optimized for project filtering
- Service integration confirmed
- Real-time monitoring validated for both projects