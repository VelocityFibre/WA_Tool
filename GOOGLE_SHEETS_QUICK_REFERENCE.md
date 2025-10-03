# Google Sheets Dual-Write - Quick Reference Card

**Date**: September 30, 2025 | **Status**: ✅ OPERATIONAL

---

## 🚀 **System Status Check** (Daily)

```bash
# 1. Check service is running
sudo systemctl status whatsapp-drop-monitor

# 2. Verify Google Sheets is enabled
sudo journalctl -u whatsapp-drop-monitor --no-pager -n 10 | grep "Google Sheets"
# Should show: "📊 Google Sheets dual-write ENABLED for: ['Velo Test']"

# 3. Check for recent activity
sudo journalctl -u whatsapp-drop-monitor --since "1 hour ago" | grep -E "(DR|drop)"
```

---

## 📊 **How It Works**

| WhatsApp Group | JID | Destination |
|---------------|-----|-------------|
| **Lawley Activation 3** | `120363418298130331@g.us` | Neon DB only ❌ |
| **Velo Test** | `120363421664266245@g.us` | Neon DB + Google Sheets ✅ |

**Google Sheet**: [1MAP Photos QA Sheet](https://docs.google.com/spreadsheets/d/1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk/edit) → "Velo Test" tab

---

## 🔧 **If Something Goes Wrong**

### **Service Not Running**
```bash
sudo systemctl restart whatsapp-drop-monitor
sudo systemctl status whatsapp-drop-monitor
```

### **Google Sheets Disabled**
```bash
# Check environment variables
echo $GSHEET_ID
echo $GOOGLE_APPLICATION_CREDENTIALS

# Test connection
cd /home/louisdup/VF/Apps/google_sheets && python test_connection.py
```

### **Drops Not Appearing in Sheets**
1. ✅ Confirm drop came from **Velo Test group** (not Lawley)
2. ✅ Check service logs: `sudo journalctl -u whatsapp-drop-monitor -n 20`
3. ✅ Look for error messages with the drop number

---

## 📋 **Key Files**

- **Main Script**: `/home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server/realtime_drop_monitor.py`
- **Service Config**: `/etc/systemd/system/whatsapp-drop-monitor.service`
- **Credentials**: `/home/louisdup/VF/Apps/google_sheets/sheets-credentials.json`
- **Full Documentation**: `/home/louisdup/VF/Apps/WA_Tool/GOOGLE_SHEETS_DUAL_WRITE_IMPLEMENTATION.md`

---

## ✅ **What's Working**

- ✅ **DR5777777** successfully synced with real checkboxes
- ✅ Sequential row insertion (rows 3, 4, 5...)
- ✅ Real-time monitoring every 15 seconds  
- ✅ Only Velo Test drops sync to sheets
- ✅ Automatic service restart on failure

**🎉 System is fully operational!**