# Quality Control Integration Guide

## Overview

The WhatsApp MCP Server includes a sophisticated **Quality Assurance Photo Review System** that automatically processes drop numbers from WhatsApp messages and creates quality control checklists for fiber installation tracking.

## 🎯 Key Features

### Automatic Drop Number Detection
- **Pattern Recognition**: Automatically detects drop numbers like "DR1748808", "DR1740820" from WhatsApp group messages
- **Real-time Processing**: Monitors WhatsApp group every 15 seconds
- **Persistent State**: Never misses messages, survives system restarts
- **Duplicate Prevention**: Smart tracking prevents reprocessing the same drop number

### Quality Control Workflow
- **Installation Records**: Automatically creates installation tracking entries
- **QA Photo Reviews**: Generates 14-step quality control checklists
- **Progress Tracking**: Real-time completed vs outstanding photo counts
- **User Management**: Assigns QA reviews to appropriate reviewers
- **Interactive Dashboard**: Web interface for quality control management

## 🚀 Quick Start

### 1. Prerequisites
Ensure you have the basic WhatsApp MCP setup running:
- Go WhatsApp Bridge (for message capture)
- Python MCP Server (for AI integration)
- Neon PostgreSQL database (for quality control data)

### 2. Database Setup
The QA Photos system requires PostgreSQL tables. These are automatically created:
- `installations` - Track drop numbers and contractor details
- `qa_photo_reviews` - 14-step quality control checklists
- `qa_review_steps` - Master list of quality control steps

### 3. Start Quality Control Monitoring

```bash
# Navigate to the server directory
cd whatsapp-mcp-server

# Install the systemd service (one-time setup)
./manage_monitor.sh install

# Start the real-time monitor
./manage_monitor.sh start

# Check status
./manage_monitor.sh status

# View live logs
./manage_monitor.sh logs
```

### 4. Access the Dashboard
Open your web browser to: **http://localhost:3000**

Toggle between:
- **Installations Grid**: Traditional drop number tracking
- **QA Photos Review**: Interactive quality control interface

## 📋 14-Step Quality Control Process

Each drop number automatically gets a quality control checklist with these steps:

### Installation Documentation Steps
1. **Property Frontage** – house, street number visible
2. **Location on Wall (Before Install)** – Show intended ONT spot + power outlet
3. **Outside Cable Span (Pole → Pigtail screw)** – Wide shot showing full span
4. **Home Entry Point – Outside** – Close-up of pigtail screw/duct entry
5. **Home Entry Point – Inside** – Inside view of same entry penetration

### Installation Process Steps  
6. **Fibre Entry to ONT (After Install)** – Show slack loop + clips/conduit
7. **Patched & Labelled Drop** – Label with Drop Number visible
8. **Overall Work Area After Completion** – ONT, fibre routing & electrical outlet

### Technical Verification Steps
9. **ONT Barcode** – Scan barcode + photo of label
10. **Mini-UPS Serial Number (Gizzu)** – Scan/enter serial + photo of label
11. **Powermeter Reading (Drop/Feeder)** – Enter dBm + photo of meter screen
12. **Powermeter at ONT (Before Activation)** – Enter dBm + photo (Acceptable: −25 to −10 dBm)

### Completion Steps
13. **Active Broadband Light** – ONT light ON + Fibertime sticker + Drop No.
14. **Customer Signature** – Collect digital signature + customer name in 1Map

## 🔧 Service Management Commands

### Monitor Management
```bash
# Service Control
./manage_monitor.sh start       # Start the monitor service
./manage_monitor.sh stop        # Stop the monitor service  
./manage_monitor.sh restart     # Restart the monitor service
./manage_monitor.sh status      # Check service status
./manage_monitor.sh logs        # View live logs

# Development & Testing
./manage_monitor.sh test        # Run in test mode (dry-run)
./manage_monitor.sh install     # Install as systemd service (one-time)
```

### System Status Check
```bash
# Check all components are running
ps aux | grep -E "(whatsapp|mcp)" | grep -v grep

# Expected processes:
# - whatsapp-bridge (Go application)
# - main.py (MCP server)
# - realtime_drop_monitor.py (Quality control monitor)
```

### 🔍 Real-time System Monitoring

The system includes comprehensive monitoring capabilities through the VF_Drops frontend:

#### Web-based Monitoring Dashboard
- **Access**: http://localhost:3000 → System Monitor tab
- **Auto-refresh**: Updates every 30 seconds automatically
- **Status Levels**: ✅ Healthy, ⚠️ Warning, ❌ Error
- **Component Breakdown**: Individual status for each system component

#### Header Status Indicator
- **Location**: Top-right corner of all pages
- **Real-time**: Updates every 60 seconds
- **Quick Status**: Instant visual health check without navigating

#### API-based Monitoring
```bash
# Get comprehensive system status
curl http://localhost:3000/api/system-status | jq

# Quick health check
curl -s http://localhost:3000/api/system-status | jq '.overall'

# Component-specific status
curl -s http://localhost:3000/api/system-status | jq '.services'
```

#### Monitoring Components Tracked
1. **WhatsApp Bridge (Go)**: Process status, PID, resource usage
2. **MCP Server (Python)**: Process count, systemd service status
3. **Drop Monitor (Python)**: Service status, last check time, state file
4. **SQLite Database**: Message count, recent activity, file health
5. **PostgreSQL Database**: Connectivity, response time, API tests

#### Troubleshooting with Monitoring
```bash
# If system shows warning/error, check specifics:
curl -s http://localhost:3000/api/system-status | jq '.services."whatsapp-bridge"'
curl -s http://localhost:3000/api/system-status | jq '.whatsapp.database'
curl -s http://localhost:3000/api/system-status | jq '.monitor.state'

# Check database activity
sqlite3 whatsapp-bridge/store/messages.db "SELECT COUNT(*) FROM messages WHERE timestamp > datetime('now', '-1 hour')"

# Monitor state freshness
stat whatsapp-mcp-server/monitor_state.json
```

## 📊 Database Integration

### Neon PostgreSQL Connection
The system connects to your Neon database for quality control data:
- **Installations table**: Drop numbers, contractors, status tracking
- **QA Photo Reviews table**: 14-step quality checklists with auto-calculated summaries
- **Real-time Updates**: Changes reflected immediately in web dashboard

### Data Flow
```
WhatsApp Message → Drop Number Detection → Database Records Creation → Web Dashboard Display
     ↓                    ↓                        ↓                      ↓
"DR1748808"    →    Pattern Match      →    Installation + QA Review   →   http://localhost:3000
```

### Sample Database Queries
```sql
-- Check recent drop numbers
SELECT drop_number, contractor_name, status 
FROM installations 
WHERE date_submitted >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date_submitted DESC;

-- View QA review progress
SELECT drop_number, user_name, completed_photos, outstanding_photos, comment
FROM qa_photo_reviews 
WHERE outstanding_photos > 5
ORDER BY outstanding_photos DESC;

-- Quality control statistics  
SELECT 
  user_name,
  COUNT(*) as total_reviews,
  AVG(completed_photos) as avg_completed,
  SUM(CASE WHEN outstanding_photos = 0 THEN 1 ELSE 0 END) as perfect_reviews
FROM qa_photo_reviews 
GROUP BY user_name
ORDER BY total_reviews DESC;
```

## 🎯 Quality Control Workflow

### For QA Reviewers
1. **New Drop Alerts**: System automatically detects and creates QA checklists
2. **Interactive Review**: Use web dashboard to check off completed steps
3. **Progress Tracking**: See real-time completed vs outstanding counts
4. **Comments & Notes**: Add quality issues or special instructions
5. **1MAP Integration**: Track when photos are loaded to 1MAP system

### For Contractors
1. **Simple Submission**: Send drop number to WhatsApp group (e.g., "DR1748808")
2. **Automatic Processing**: System immediately creates tracking records
3. **Quality Visibility**: Can see their QA requirements through dashboard
4. **Progress Updates**: Real-time feedback on photo completion status

### For Managers
1. **Overview Dashboard**: See all active installations and quality status
2. **Performance Metrics**: Track completion rates by contractor and reviewer
3. **Quality Trends**: Identify common quality issues across installations
4. **Automated Workflow**: No manual data entry or tracking required

## 🔍 Troubleshooting

### Common Issues

**Monitor Not Running**
```bash
./manage_monitor.sh status
# If inactive, restart with:
./manage_monitor.sh restart
```

**Missed Drop Numbers**
Check the monitor state and logs:
```bash
cat monitor_state.json          # Check last processing time
./manage_monitor.sh logs        # View recent activity
```

**Database Connection Issues**
Verify database connectivity:
```bash
# Test database connection manually
cd whatsapp-mcp-server
uv run python -c "
import psycopg2
conn = psycopg2.connect('YOUR_NEON_URL')
print('Database connection OK')
"
```

**Frontend Not Loading**
Check if the VF_Drops application is running:
```bash
# Should be accessible at http://localhost:3000
curl http://localhost:3000/api/installations
```

### Log Analysis
Monitor logs show detailed processing information:
```bash
# View recent monitor activity
./manage_monitor.sh logs

# Search for specific drop numbers
sudo journalctl -u whatsapp-drop-monitor | grep "DR1748808"

# Check for errors
sudo journalctl -u whatsapp-drop-monitor | grep -i error
```

### State Management
The monitor maintains persistent state in `monitor_state.json`:
```json
{
  "last_check_time": "2025-09-26T10:42:11.638985",
  "processed_message_ids": ["ACAA576FFD6C19B4C83172230C833DDC"],
  "saved_at": "2025-09-26T10:42:11.639008"
}
```

## 🚀 Advanced Configuration

### Monitor Settings
Edit `realtime_drop_monitor.py` to customize:
- **Check Interval**: Default 15 seconds
- **WhatsApp Group**: Target group JID
- **Drop Pattern**: Regex for drop number recognition
- **Database URLs**: Neon PostgreSQL connection

### QA Review Customization
Modify the 14 quality control steps by updating:
- `qa_review_steps` table in PostgreSQL
- Frontend grid columns in `QAPhotosGrid.tsx`
- Database schema in `qa-photos-schema.sql`

### Integration Extensions
The system is designed for easy extension:
- **Photo Upload**: Add file upload capability to QA steps
- **Mobile App**: Create mobile QA review interface  
- **API Integration**: Connect to 1MAP or other external systems
- **Notifications**: Email/SMS alerts for quality issues
- **Reporting**: Advanced analytics and performance dashboards

## 📈 Performance & Scaling

### System Resources
- **Memory**: ~50MB for monitor process
- **CPU**: Minimal (<1% on average)
- **Database**: Efficient indexing for large datasets
- **Network**: Lightweight WhatsApp API calls

### Scaling Considerations
- **Multiple Groups**: Can monitor multiple WhatsApp groups simultaneously
- **High Volume**: Handles hundreds of drop numbers per day
- **Database Growth**: Automatic cleanup of old processed messages
- **Load Balancing**: Can run multiple monitor instances if needed

## 🔐 Security & Privacy

### Data Protection
- **Local Storage**: WhatsApp messages stored locally in SQLite
- **Encrypted Connections**: All database connections use SSL/TLS
- **Access Control**: QA dashboard requires local network access
- **Message Retention**: Configurable retention policies

### WhatsApp Authentication
- **QR Code Auth**: Secure WhatsApp Web authentication
- **Session Persistence**: Re-authentication needed ~every 20 days
- **Device Limits**: WhatsApp restricts number of linked devices

---

## 📞 Support

For technical support or questions about the Quality Control system:

1. **Check Service Status**: `./manage_monitor.sh status`
2. **Review Logs**: `./manage_monitor.sh logs`
3. **Verify Database**: Check Neon PostgreSQL connection
4. **Test Frontend**: Access http://localhost:3000
5. **State Analysis**: Examine `monitor_state.json`

The Quality Control integration provides end-to-end automation from WhatsApp message detection to quality assurance completion tracking, ensuring no drop numbers are missed and maintaining high quality standards for fiber installation processes.