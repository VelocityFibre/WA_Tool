# Drop Number Extraction Guide

## Quick Commands

### Get Today's Drop Numbers
```bash
cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server
uv run python extract_drops.py --today
```

### Get Last 7 Days Drop Numbers (Default)
```bash
uv run python extract_drops.py
```

### Get Last N Days Drop Numbers
```bash
uv run python extract_drops.py --days 3
```

### Get Drop Numbers in CSV Format
```bash
uv run python extract_drops.py --format csv
```

### Get Drop Numbers in JSON Format
```bash
uv run python extract_drops.py --format json
```

## Current Status

✅ **WhatsApp Connected**: Lawley Activation 3 group is accessible  
✅ **Latest Drop Number Confirmed**: DR1750813 (from today, 2025-09-26 08:40:23)  
✅ **Group JID**: 120363418298130331@g.us  

## Recent Drop Numbers (Last 3 Days)

From most recent to oldest:
- DR1750813 (2025-09-26 08:40:23) - Latest
- DR1751085 (2025-09-25 19:40:26)
- DR1751078 (2025-09-25 18:42:02)
- DR1751056 (2025-09-25 18:40:46)
- DR1751055 (2025-09-25 18:40:30)
- DR1751075 (2025-09-25 18:21:39)
- DR1748835 (2025-09-25 18:21:34)
- DR1748807 (2025-09-25 18:10:45)
- DR1748890 (2025-09-25 17:23:58)
- DR1751313 (2025-09-25 17:10:28)
- DR1748852 (2025-09-25 17:08:56)
- DR1748801 (2025-09-25 16:59:27)
- DR1748802 (2025-09-25 16:49:35)
- DR1748811 (2025-09-25 16:31:57)
- DR1748816 (2025-09-25 16:08:58)

## For Grid Updates

**Comma-separated format (copy-paste ready):**
```
DR1750813, DR1751085, DR1751078, DR1751056, DR1751055, DR1751075, DR1748835, DR1748807, DR1748890, DR1751313, DR1748852, DR1748801, DR1748802, DR1748811, DR1748816
```

## Troubleshooting

If the script doesn't work:

1. **Ensure WhatsApp bridge is running:**
   ```bash
   cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-bridge
   go run main.go
   ```

2. **Check if MCP server dependencies are installed:**
   ```bash
   cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server
   uv sync
   ```

3. **Test WhatsApp connection:**
   ```bash
   uv run python -c "from whatsapp import list_chats; print(list_chats(query='Lawley', limit=2))"
   ```

## Automation Ideas

You could create a cron job or scheduled task to run this daily:

```bash
# Add to crontab (run daily at 9 AM):
0 9 * * * cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server && /path/to/uv run python extract_drops.py --today >> /path/to/daily_drops.log 2>&1
```