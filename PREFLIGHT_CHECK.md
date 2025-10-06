# 🚀 WA Tool Pre-Flight Check - Complete Functionality Verification

**Purpose**: Verify ACTUAL functionality, not just container status
**Created**: October 6, 2025
**Reason**: Prevent false confirmations by checking real data flow

---

## ❌ **WHAT I WAS CHECKING WRONG BEFORE:**
- ✅ Container running status (meaningless)
- ✅ API responding with 404 (meaningless) 
- ✅ Log startup messages (meaningless)

## ✅ **WHAT ACTUALLY MATTERS - REAL FUNCTIONALITY:**

### **1. WhatsApp Bridge Functionality Check**
```bash
# Check if messages are ACTUALLY being stored in SQLite
docker exec wa-bridge-privacy sqlite3 /app/store/messages.db "
SELECT COUNT(*) as total_messages,
       MAX(timestamp) as latest_message_time
FROM messages;"

# Check if recent messages exist (last 30 minutes)
docker exec wa-bridge-privacy sqlite3 /app/store/messages.db "
SELECT timestamp, sender, content 
FROM messages 
WHERE datetime(timestamp) > datetime('now', '-30 minutes')
ORDER BY timestamp DESC
LIMIT 5;"
```

### **2. Drop Monitor Functionality Check**
```bash
# Check if monitor is ACTUALLY processing new messages
docker logs wa-drop-monitor --since="5m" | grep -E "(Found.*messages|Processing|DR[0-9])"

# Check monitor state file for recent activity
docker exec wa-drop-monitor ls -la /app/ | grep state
docker exec wa-drop-monitor cat /app/realtime_drop_monitor_state.json
```

### **3. Google Sheets Connectivity Check**
```bash
# Test actual Google Sheets read/write
docker exec wa-drop-monitor python -c "
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

try:
    credentials = Credentials.from_service_account_file(
        '/app/credentials.json', 
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    service = build('sheets', 'v4', credentials=credentials)
    
    # Try to read actual sheet data
    result = service.spreadsheets().values().get(
        spreadsheetId='1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk',
        range='Velo Test!A1:B5'
    ).execute()
    
    print('✅ Google Sheets READ test successful')
    print(f'Data retrieved: {len(result.get("values", []))} rows')
except Exception as e:
    print(f'❌ Google Sheets test failed: {e}')
"
```

### **4. Neon Database Connectivity Check**
```bash
# Test actual database connection and recent data
docker exec wa-drop-monitor python -c "
import psycopg2
import os

try:
    conn = psycopg2.connect(os.getenv('NEON_DB_URL'))
    cursor = conn.cursor()
    
    # Check recent installations
    cursor.execute('SELECT COUNT(*) FROM installations WHERE created_at > NOW() - INTERVAL \'1 hour\'')
    recent_count = cursor.fetchone()[0]
    
    # Check recent QA reviews  
    cursor.execute('SELECT COUNT(*) FROM qa_photo_reviews WHERE created_at > NOW() - INTERVAL \'1 hour\'')
    qa_count = cursor.fetchone()[0]
    
    print(f'✅ Neon DB connected')
    print(f'Recent installations: {recent_count}')
    print(f'Recent QA reviews: {qa_count}')
    
    conn.close()
except Exception as e:
    print(f'❌ Neon DB test failed: {e}')
"
```

### **5. End-to-End Data Flow Test**
```bash
# POST TEST MESSAGE and trace it through entire system
echo "=== POSTING TEST MESSAGE ==="
echo "Manual step: Post 'DR9999999' to Velo Test WhatsApp group"
echo "Then run these checks:"

echo "1. Check if message stored in SQLite (within 30 seconds):"
echo "docker exec wa-bridge-privacy sqlite3 /app/store/messages.db \"SELECT timestamp, content FROM messages WHERE content LIKE '%DR9999999%' ORDER BY timestamp DESC LIMIT 1;\""

echo "2. Check if drop monitor processed it (within 60 seconds):"
echo "docker logs wa-drop-monitor --since='2m' | grep DR9999999"

echo "3. Check if written to Neon (within 90 seconds):"
echo "docker exec wa-drop-monitor python -c \"import psycopg2, os; conn = psycopg2.connect(os.getenv('NEON_DB_URL')); cursor = conn.cursor(); cursor.execute('SELECT * FROM installations WHERE drop_number = %s', ('DR9999999',)); print(cursor.fetchone())\""

echo "4. Check if written to Google Sheets (within 90 seconds):"
echo "Check: https://docs.google.com/spreadsheets/d/1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk/edit"
```

---

## 🎯 **COMPREHENSIVE PRE-FLIGHT CHECKLIST**

### **Phase 1: Infrastructure**
- [ ] All containers running (basic check)
- [ ] Portainer accessible at https://172.20.10.2:9443
- [ ] Container logs show no critical errors in last 5 minutes

### **Phase 2: Data Connectivity** 
- [ ] SQLite database exists and is writable
- [ ] Neon PostgreSQL connection working with actual query
- [ ] Google Sheets API connection working with actual read/write test
- [ ] WhatsApp Bridge session authenticated and stable

### **Phase 3: Message Processing**
- [ ] WhatsApp messages being stored in SQLite (test with recent timestamp check)
- [ ] Drop monitor reading from SQLite and finding messages
- [ ] Drop monitor state file updating with recent timestamps
- [ ] No decryption/session errors in WhatsApp Bridge logs

### **Phase 4: Business Logic**
- [ ] New drop numbers being detected from test messages
- [ ] Dual-write to Neon + Google Sheets actually working
- [ ] QA review records being created automatically
- [ ] Drop numbers appearing in correct Google Sheet tab within 90 seconds

### **Phase 5: End-to-End Verification**
- [ ] Post test drop number to WhatsApp
- [ ] Verify it appears in SQLite within 30 seconds
- [ ] Verify it appears in Neon DB within 60 seconds  
- [ ] Verify it appears in Google Sheets within 90 seconds
- [ ] Verify QA review record created in Neon

---

## 🚨 **CRITICAL SUCCESS CRITERIA**

**SYSTEM IS ONLY CONFIRMED WORKING WHEN:**
1. Test message posted to WhatsApp appears in Google Sheet within 2 minutes
2. All 3 databases (SQLite, Neon, Sheets) show the same test data
3. No error messages in any container logs during test
4. QA workflow can be triggered by ticking "Incomplete" checkbox

**IF ANY OF ABOVE FAILS → SYSTEM IS NOT WORKING**

---

## 📊 **AUTOMATED FULL CHECK SCRIPT**

```bash
#!/bin/bash
# File: run_preflight_check.sh

echo "🚀 WA TOOL PREFLIGHT CHECK - FULL FUNCTIONALITY"
echo "================================================="

# Phase 1: Basic Infrastructure
echo "Phase 1: Container Status"
docker ps --filter "name=wa-" --format "table {{.Names}}\t{{.Status}}"

# Phase 2: Database Connectivity Tests
echo -e "\nPhase 2: Database Tests"
docker exec wa-drop-monitor python /app/preflight_db_test.py

# Phase 3: WhatsApp Session Health
echo -e "\nPhase 3: WhatsApp Bridge Health"
docker logs wa-bridge-privacy --since="5m" | tail -3

# Phase 4: Recent Activity Check
echo -e "\nPhase 4: Recent Message Activity"
docker exec wa-bridge-privacy sqlite3 /app/store/messages.db "
SELECT 'Messages in last hour: ' || COUNT(*) FROM messages 
WHERE datetime(timestamp) > datetime('now', '-1 hour');"

echo -e "\n🎯 MANUAL TEST REQUIRED:"
echo "Post 'DR9999999' to Velo Test group and verify it appears in Google Sheets within 90 seconds"
echo "Sheet: https://docs.google.com/spreadsheets/d/1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk/edit"
```

---

## 🔧 **RECOMMENDATION**

1. **Run this full preflight check EVERY TIME** before confirming system is working
2. **Never confirm based on container status alone**  
3. **Always test end-to-end with actual WhatsApp message**
4. **Check all 3 data stores (SQLite, Neon, Sheets) contain same data**
5. **Use Portainer for visual monitoring of container health**

**This prevents the false confirmations that happened before.**