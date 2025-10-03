#!/usr/bin/env python3
import sqlite3
import time
import subprocess
import sys

# Quick kill switch - monitors for KILL command
WHATSAPP_DB = "whatsapp-mcp/whatsapp-bridge/store/messages.db"
GROUP_JID = "120363421664266245@g.us"  # Velo Test

def check_kill():
    try:
        conn = sqlite3.connect(WHATSAPP_DB)
        cursor = conn.cursor()
        
        # Check last 5 minutes for KILL command
        since = time.time() - 300
        cursor.execute("""
            SELECT content, sender, timestamp FROM messages 
            WHERE chat_jid = ? AND timestamp > ? 
            AND UPPER(content) LIKE '%KILL%'
            ORDER BY timestamp DESC LIMIT 1
        """, (GROUP_JID, since))
        
        result = cursor.fetchone()
        if result:
            print(f"🚨 KILL COMMAND DETECTED: {result[0]}")
            print("🛑 SHUTTING DOWN ALL SERVICES...")
            subprocess.run(["docker-compose", "down", "--remove-orphans"])
            sys.exit(0)
        
    except Exception as e:
        print(f"Kill check error: {e}")

if __name__ == "__main__":
    print("🚨 Kill switch active...")
    while True:
        check_kill()
        time.sleep(3)