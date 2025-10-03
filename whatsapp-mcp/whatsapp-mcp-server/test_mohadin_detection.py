#!/usr/bin/env python3
"""
Test script to verify Mohadin message detection works correctly after the timestamp fix.
"""

import sqlite3
from datetime import datetime, timezone, timedelta
import re

MESSAGES_DB_PATH = '../whatsapp-bridge/store/messages.db'
MOHADIN_JID = '120363421532174586@g.us'
DROP_PATTERN = r'DR\d+'

def test_timestamp_query():
    print("=== Testing Mohadin Message Detection ===\n")
    
    # Test with a timestamp that should capture recent messages
    test_timestamp = datetime.now() - timedelta(hours=2)
    
    # Add timezone info as the fix does
    if test_timestamp.tzinfo is None:
        test_timestamp = test_timestamp.replace(tzinfo=timezone(timedelta(hours=2)))
    
    timestamp_str = test_timestamp.strftime('%Y-%m-%d %H:%M:%S%z')
    # Convert to format that matches database (with colon in timezone)
    if len(timestamp_str) > 19 and timestamp_str[-2:].isdigit():
        timestamp_str = timestamp_str[:-2] + ':' + timestamp_str[-2:]
    
    print(f"Query timestamp: {timestamp_str}")
    print(f"Mohadin group JID: {MOHADIN_JID}")
    
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        # Query using the same logic as the fixed monitor
        cursor.execute("""
            SELECT id, content, sender, timestamp, is_from_me
            FROM messages 
            WHERE chat_jid = ? AND timestamp > ? AND content != ''
            ORDER BY timestamp ASC
        """, (MOHADIN_JID, timestamp_str))
        
        messages = cursor.fetchall()
        print(f"\nFound {len(messages)} Mohadin messages since {timestamp_str}")
        
        dr_count = 0
        for msg in messages:
            msg_id, content, sender, timestamp, is_from_me = msg
            has_dr = bool(re.search(DROP_PATTERN, content, re.IGNORECASE))
            if has_dr:
                dr_count += 1
                print(f"  ✅ DR FOUND: {msg_id[:20]}... | {content[:50]:<50} | {timestamp}")
            else:
                print(f"     {msg_id[:20]}... | {content[:50]:<50} | {timestamp}")
        
        print(f"\n🎯 Found {dr_count} messages with DR numbers out of {len(messages)} total messages")
        
        # Also test with the old format (without timezone) to show the difference
        print("\n=== Comparison with old timestamp format ===")
        old_timestamp_str = test_timestamp.strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            SELECT COUNT(*)
            FROM messages 
            WHERE chat_jid = ? AND timestamp > ? AND content != ''
        """, (MOHADIN_JID, old_timestamp_str))
        
        old_count = cursor.fetchone()[0]
        print(f"Old format ({old_timestamp_str}): {old_count} messages")
        print(f"New format ({timestamp_str}): {len(messages)} messages")
        print(f"Difference: {len(messages) - old_count} additional messages detected!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_timestamp_query()