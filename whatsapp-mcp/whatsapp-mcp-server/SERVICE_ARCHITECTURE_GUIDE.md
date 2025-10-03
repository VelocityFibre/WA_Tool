# WA_Tool Service Architecture & Monitoring Guide
**Date**: October 1, 2025
**Version**: 1.0.0

## 📋 Overview

The WA_Tool system monitors WhatsApp messages from three groups:
- **Lawley Activation 3** (`120363418298130331@g.us`)
- **Velo Test** (`120363421664266245@g.us`)
- **Mohadin Activations** (`120363421532174586@g.us`)

## 🏗️ Service Architecture

### Core Services

#### 1. WhatsApp Bridge Service
- **Purpose**: Bridge between WhatsApp Web and monitoring system
- **Location**: `../whatsapp-bridge/whatsapp-bridge`
- **Critical**: ✅ Yes (All services depend on this)
- **Status**: Must be running at all times

#### 2. Real-time Drop Monitor
- **Script**: `realtime_drop_monitor.py`
- **Purpose**: Extract DR numbers from all groups and sync to:
  - Neon PostgreSQL database
  - Google Sheets (separate tabs per group)
- **Interval**: 15 seconds
- **Groups**: Lawley, Velo Test, Mohadin
- **Critical**: ✅ Yes

#### 3. Google Sheets QA Monitor
- **Script**: `google_sheets_qa_monitor.py`
- **Purpose**: Monitor Google Sheets for incomplete drops and send WhatsApp feedback
- **Interval**: 60 seconds
- **Groups**: Velo Test, Mohadin
- **Critical**: ✅ Yes

#### 4. WhatsApp Message Monitor (Velo Test)
- **Script**: `whatsapp_message_monitor.py`
- **Purpose**: Monitor Velo Test for resubmission keywords
- **Interval**: 30 seconds
- **Group**: Velo Test only
- **Critical**: ❌ No (Optional feature)

#### 5. WhatsApp Message Monitor (Mohadin)
- **Script**: `mohadin_message_monitor.py`
- **Purpose**: Monitor Mohadin for resubmission keywords
- **Interval**: 30 seconds
- **Group**: Mohadin only
- **Critical**: ❌ No (Optional feature)

## 🚀 Startup Procedures

### Manual Startup
```bash
# 1. Start WhatsApp Bridge
cd ../whatsapp-bridge
./whatsapp-bridge

# 2. Start monitoring services (in separate terminals)
cd ../whatsapp-mcp-server
source .venv/bin/activate

# Critical services
python realtime_drop_monitor.py --interval 15 &
python google_sheets_qa_monitor.py --interval 60 &

# Optional services
python whatsapp_message_monitor.py --interval 30 &
python mohadin_message_monitor.py --interval 30 &
```

### Automated Startup
```bash
# Use the startup script
./start_all_services.sh
```

## 📊 Monitoring Dashboard

### Streamlit Dashboard
- **File**: `service_monitor.py`
- **Purpose**: Real-time monitoring of all services
- **Features**:
  - Service status (running/stopped)
  - Process ID tracking
  - Recent log entries
  - Database statistics
  - Group activity monitoring

### To Start Dashboard
```bash
# Install requirements (first time only)
pip install -r requirements_dashboard.txt

# Start dashboard
streamlit run service_monitor.py
```

**Access**: http://localhost:8501

## 🔍 Service Status Checking

### Command Line Check
```bash
# Check all running processes
ps aux | grep -E "(whatsapp|mohadin|velo|monitor)" | grep -v grep

# Check specific service
pgrep -f "realtime_drop_monitor.py"
```

### Log Monitoring
```bash
# Real-time logs
tail -f realtime_monitor.log
tail -f google_sheets_qa_monitor.log
tail -f whatsapp_message_monitor.log
tail -f mohadin_message_monitor.log

# WhatsApp bridge logs
tail -f ../whatsapp-bridge/bridge.log
```

## 📁 File Structure

```
WA_Tool/
├── whatsapp-mcp/whatsapp-bridge/
│   ├── whatsapp-bridge                 # Core bridge executable
│   ├── store/
│   │   ├── messages.db                # SQLite database
│   │   └── bridge.log                 # Bridge logs
│   └── whatsapp.db                    # WhatsApp state

├── whatsapp-mcp/whatsapp-mcp-server/
│   ├── realtime_drop_monitor.py       # DR number extraction
│   ├── google_sheets_qa_monitor.py   # Sheet monitoring
│   ├── whatsapp_message_monitor.py    # Velo Test resubmissions
│   ├── mohadin_message_monitor.py     # Mohadin resubmissions
│   ├── sync_drops_to_neon.py         # Manual sync script
│   ├── qa_feedback_communicator.py   # WhatsApp feedback
│   ├── service_monitor.py             # Streamlit dashboard
│   ├── start_all_services.sh          # Startup script
│   ├── monitor_state.json             # Monitor state
│   └── *.log                          # Log files
```

## ⚙️ Configuration

### Environment Variables Required
```bash
export GSHEET_ID="your_google_sheet_id"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"
```

### Database Configuration
- **Neon Database**: Configured in `sync_drops_to_neon.py`
- **SQLite Database**: `../whatsapp-bridge/store/messages.db`

## 🚨 Troubleshooting

### Common Issues

#### 1. WhatsApp Bridge Not Running
**Symptoms**: No messages being captured
**Solution**:
```bash
cd ../whatsapp-bridge
./whatsapp-bridge
# Check bridge.log for errors
```

#### 2. Foreign Key Constraint Errors
**Symptoms**: Messages not storing in database
**Solution**: Add missing group to chats table:
```bash
sqlite3 ../whatsapp-bridge/store/messages.db
INSERT INTO chats (jid, name, project_name)
VALUES ('GROUP_JID@g.us', 'Group Name', 'ProjectName');
```

#### 3. Google Sheets Not Updating
**Symptoms**: DR numbers not appearing in sheets
**Solution**:
- Check `GSHEET_ID` environment variable
- Verify Google credentials file
- Check `google_sheets_qa_monitor.log`

#### 4. Services Keep Stopping
**Symptoms**: Services start then stop immediately
**Solution**:
- Check log files for error messages
- Verify Python environment: `source .venv/bin/activate`
- Check dependencies: `pip install -r requirements.txt`

### Log Analysis
```bash
# Find recent errors
grep -i "error\|exception\|failed" *.log | tail -10

# Monitor for specific patterns
grep -i "DR.*[0-9]" realtime_monitor.log | tail -5

# Check service restarts
grep "Starting\|Stopping\|Restarting" *.log
```

## 🔄 Auto-start Configuration

### Systemd Service (Optional)
Create systemd services for automatic startup on boot:

**Example**: `/etc/systemd/system/whatsapp-bridge.service`
```ini
[Unit]
Description=WhatsApp Bridge Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/WA_Tool/whatsapp-mcp/whatsapp-bridge
ExecStart=/home/ubuntu/WA_Tool/whatsapp-mcp/whatsapp-bridge/whatsapp-bridge
Restart=always

[Install]
WantedBy=multi-user.target
```

### Cron Jobs (Alternative)
```bash
# Edit crontab
crontab -e

# Add monitoring checks
*/5 * * * * /home/ubuntu/WA_Tool/whatsapp-mcp/whatsapp-mcp-server/check_services.sh
```

## 📈 Performance Monitoring

### Resource Usage
```bash
# Memory usage
ps aux | grep python | awk '{print $4, $11}' | sort -nr

# CPU usage
top -p $(pgrep -d',' -f "python.*monitor")

# Disk usage
du -sh *.log
```

### Database Health
```bash
# Check database size
ls -lh ../whatsapp-bridge/store/messages.db

# Check table counts
sqlite3 ../whatsapp-bridge/store/messages.db "SELECT 'Messages:', COUNT(*) FROM messages UNION SELECT 'Chats:', COUNT(*) FROM chats;"
```

## 🎯 Best Practices

1. **Monitor Dashboard**: Check Streamlit dashboard regularly
2. **Log Rotation**: Implement log rotation to prevent disk space issues
3. **Backups**: Regular backups of SQLite database
4. **Service Health**: Monitor service restarts
5. **Dependencies**: Keep Python packages updated
6. **Security**: Regular security updates for system packages

## 📞 Support

For issues or questions:
1. Check log files for error messages
2. Verify all services are running
3. Check environment variables
4. Review this documentation
5. Contact system administrator

---

**Last Updated**: October 1, 2025
**Next Review**: November 1, 2025