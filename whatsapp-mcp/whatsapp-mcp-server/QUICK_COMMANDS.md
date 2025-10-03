# WhatsApp Drop Monitoring - Quick Commands

## 🚀 **Real-time Monitor (NEW!)**

```bash
# Navigate to project
cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server

# Test first (recommended)
./manage_monitor.sh test

# Install & start real-time monitoring
./manage_monitor.sh install
./manage_monitor.sh start

# Monitor status
./manage_monitor.sh status
./manage_monitor.sh logs

# Control service
./manage_monitor.sh stop
./manage_monitor.sh restart
```

## 📱 **Manual Drop Extraction**

```bash
# Get today's drops
uv run python extract_drops.py --today

# Get last 3 days
uv run python extract_drops.py --days 3

# Get in CSV format
uv run python extract_drops.py --format csv
```

## 💾 **Manual Database Sync**

```bash
# Sync today's drops
uv run python sync_drops_to_neon.py --today

# Sync last 3 days
uv run python sync_drops_to_neon.py --days 3

# Preview changes first
uv run python sync_drops_to_neon.py --today --dry-run
```

## 🔧 **System Status Checks**

```bash
# Check WhatsApp connection
uv run python -c "from whatsapp import list_chats; print([c.name for c in list_chats(query='Lawley', limit=2)])"

# Check database records
psql 'postgresql://neondb_owner:npg_RIgDxzo4St6d@ep-damp-credit-a857vku0-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require' -c "SELECT COUNT(*) as total, COUNT(*) FILTER (WHERE drop_number LIKE 'DR%') as dr_count FROM installations;"

# Check WhatsApp bridge
cd ../whatsapp-bridge && go run main.go
```

## ⚡ **Current Drop Numbers in Database**

```sql
-- View all DR drops
SELECT drop_number, contractor_name, status, date_submitted 
FROM installations 
WHERE drop_number LIKE 'DR%' 
ORDER BY date_submitted DESC;
```

## 🎯 **What's Running Now**

✅ **Real-time Monitor**: Checks every 15 seconds for new drops  
✅ **Auto-sync**: New drops added to database instantly  
✅ **Notifications**: Alerts logged when new drops detected  
✅ **Database**: 25 total installations (15 DR + 10 VF)  
✅ **WhatsApp**: Connected to Lawley Activation 3 group  

---

## 🚨 **Emergency Commands**

```bash
# If monitor stops working
./manage_monitor.sh restart

# If database connection fails
psql 'postgresql://neondb_owner:npg_RIgDxzo4St6d@ep-damp-credit-a857vku0-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require' -c "SELECT 1;"

# If WhatsApp bridge is down
cd ../whatsapp-bridge && go run main.go

# View monitor logs
sudo journalctl -u whatsapp-drop-monitor -f
```

**You're all set for real-time drop number monitoring! 🎉**