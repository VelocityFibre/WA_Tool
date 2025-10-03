# Neon Database Sync Guide

## Quick Commands for Database Sync

### Sync Today's Drop Numbers
```bash
cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server
uv run python sync_drops_to_neon.py --today
```

### Sync Last 3 Days Drop Numbers
```bash
uv run python sync_drops_to_neon.py --days 3
```

### Preview Changes (Dry Run)
```bash
uv run python sync_drops_to_neon.py --days 7 --dry-run
```

## Database Status ✅

**Connection**: Successfully connected to Neon PostgreSQL  
**Database**: `neondb` on `eastus2.azure.neon.tech`  
**Table**: `installations`  
**Total Records**: 25 installations  
- **DR Drop Numbers**: 15 (from WhatsApp)  
- **VF Drop Numbers**: 10 (existing records)  

## Recently Added Drop Numbers

All 15 drop numbers from Lawley Activation 3 group have been successfully added:

| Drop Number | Contractor | Status | Added |
|-------------|------------|--------|-------|
| DR1750813 | WhatsApp-199209844252927 | submitted | 2025-09-26 |
| DR1751085 | WhatsApp-110939525410979@lid | submitted | 2025-09-26 |
| DR1751078 | WhatsApp-110939525410979@lid | submitted | 2025-09-26 |
| DR1751056 | WhatsApp-181789406531737@lid | submitted | 2025-09-26 |
| DR1751055 | WhatsApp-181789406531737@lid | submitted | 2025-09-26 |
| DR1751075 | WhatsApp-110939525410979@lid | submitted | 2025-09-26 |
| DR1748835 | WhatsApp-254404401832045@lid | submitted | 2025-09-26 |
| DR1748807 | WhatsApp-220551134097426@lid | submitted | 2025-09-26 |
| DR1748890 | WhatsApp-80333605232852@lid | submitted | 2025-09-26 |
| DR1751313 | WhatsApp-160314653982720@lid | submitted | 2025-09-26 |
| DR1748852 | WhatsApp-235493459497046@lid | submitted | 2025-09-26 |
| DR1748801 | WhatsApp-80333605232852@lid | submitted | 2025-09-26 |
| DR1748802 | WhatsApp-220551134097426@lid | submitted | 2025-09-26 |
| DR1748811 | WhatsApp-80333605232852@lid | submitted | 2025-09-26 |
| DR1748816 | WhatsApp-110939525410979@lid | submitted | 2025-09-26 |

## Key Features

### ✅ Duplicate Prevention
- Script checks for existing drop numbers
- Prevents duplicate insertions
- Shows skipped duplicates in output

### ✅ WhatsApp Integration
- Extracts drop numbers from Lawley Activation 3 group
- Preserves original timestamps and sender info
- Maps WhatsApp senders to contractor names

### ✅ Database Schema Compliance
- Uses proper status values ('submitted', 'under_review', 'complete', 'incomplete', 'unpaid')
- Includes agent notes with import details
- Auto-generates timestamps

## Manual Database Queries

### Check DR Drop Numbers
```sql
SELECT drop_number, contractor_name, status, date_submitted 
FROM installations 
WHERE drop_number LIKE 'DR%' 
ORDER BY date_submitted DESC;
```

### Count by Type
```sql
SELECT 
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE drop_number LIKE 'DR%') as dr_count,
    COUNT(*) FILTER (WHERE drop_number LIKE 'VF%') as vf_count
FROM installations;
```

### Recent Submissions
```sql
SELECT drop_number, contractor_name, date_submitted
FROM installations 
WHERE date_submitted >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY date_submitted DESC;
```

## Automation Ideas

### Daily Sync Cron Job
```bash
# Add to crontab to sync daily at 10 AM:
0 10 * * * cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server && /path/to/uv run python sync_drops_to_neon.py --today >> /path/to/sync.log 2>&1
```

### Hourly Check for New Drops
```bash
# Check every hour for new drops:
0 * * * * cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server && /path/to/uv run python sync_drops_to_neon.py --today --dry-run | grep "New drops to insert: [1-9]" && /path/to/uv run python sync_drops_to_neon.py --today
```

## Troubleshooting

### Connection Issues
```bash
# Test database connection directly:
psql 'postgresql://neondb_owner:npg_RIgDxzo4St6d@ep-damp-credit-a857vku0-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require' -c "SELECT COUNT(*) FROM installations;"
```

### Dependencies
```bash
# Ensure psycopg2 is installed:
cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server
uv add psycopg2-binary
```

### WhatsApp Connection
```bash
# Test WhatsApp extraction:
uv run python extract_drops.py --today
```

## Next Steps

1. **Monitor Daily**: Run sync daily to catch new drop numbers
2. **Update Status**: Manually update status in database as work progresses
3. **Add Details**: Use database interface to add customer info, addresses, etc.
4. **Reports**: Query database for progress reports and analytics