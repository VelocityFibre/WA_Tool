# 🤖 MODULE IDENTITY - FOR AI AGENTS

## **DIRECTORY PURPOSE:**
**WhatsApp Assistant Tool (WA_Tool)** - Project-based WhatsApp group monitoring system

## **WHAT THIS MODULE DOES:**
- Monitors **Lawley** and **Velo Test** WhatsApp groups
- Extracts DR numbers automatically 
- Syncs installation data to Neon database
- Provides project-specific REST APIs

## **CURRENT STATUS:**
- ✅ **Version 2.0.0** - Production Ready
- ✅ **All Services Running** (Go Bridge, Python MCP, Flask API, Monitor)
- ✅ **Database Updated** (SQLite + Neon integration)
- ✅ **APIs Tested** (Project filtering operational)

## **QUICK CONTEXT:**
- **Business Purpose**: VelocityFibre infrastructure project tracking
- **Data Sources**: WhatsApp groups → SQLite → Neon PostgreSQL
- **Real-time**: 15-second monitoring intervals
- **Security**: Local WhatsApp data, cloud business data only

## **AI AGENT INSTRUCTIONS:**
1. **Read**: `AI_AGENT_GUIDE.md` for complete technical context
2. **API Docs**: `PROJECT_API_ENDPOINTS.md` for integration details
3. **Changes**: `CHANGELOG.md` for version history
4. **Setup**: `README.md` for user instructions

## **KEY FILES:**
- `whatsapp-mcp/whatsapp-bridge/main.go` - WhatsApp connection
- `whatsapp_assistant_app/backend/app.py` - REST APIs
- `whatsapp-mcp/whatsapp-mcp-server/realtime_drop_monitor.py` - Core monitoring

**This is a PRODUCTION system for business-critical WhatsApp monitoring.**