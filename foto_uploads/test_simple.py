#!/usr/bin/env python3
"""
Quick test for simple photo upload
"""

import sqlite3
from pathlib import Path
from simple_upload import WHATSAPP_DB, GROUPS, parse_message, QA_STEPS

def test_database():
    """Test if we can read WhatsApp database"""
    print("🔍 Testing WhatsApp database...")
    
    if not WHATSAPP_DB.exists():
        print(f"❌ Database not found: {WHATSAPP_DB}")
        return False
    
    try:
        conn = sqlite3.connect(str(WHATSAPP_DB))
        cursor = conn.cursor()
        
        # Check groups have messages
        for group_jid, project in GROUPS.items():
            cursor.execute("""
                SELECT COUNT(*) FROM messages 
                WHERE chat_jid = ? AND media_type = 'image'
            """, (group_jid,))
            
            count = cursor.fetchone()[0]
            print(f"📊 {project}: {count} image messages total")
        
        conn.close()
        print("✅ Database OK")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_message_parsing():
    """Test message parsing logic"""
    print("\n🧪 Testing message parsing...")
    
    test_messages = [
        "DR1748808 Step 1 Property frontage photo",
        "DR123456 step 9: ONT barcode",
        "Step 14 customer signature DR999999",
        "DR555555 Step 12 Image 2 power reading",
        "Just a photo without info",
        "DR123456 without step",
        "Step 5 without drop number"
    ]
    
    for msg in test_messages:
        result = parse_message(msg)
        if result:
            step_name = QA_STEPS.get(result['qa_step'], 'Unknown')
            print(f"✅ '{msg}' → {result['drop_number']} Step {result['qa_step']} ({step_name})")
        else:
            print(f"❌ '{msg}' → Invalid")
    
    return True

def test_recent_messages():
    """Show recent messages that would be processed"""
    print("\n📋 Recent image messages with content...")
    
    if not WHATSAPP_DB.exists():
        return False
    
    conn = sqlite3.connect(str(WHATSAPP_DB))
    cursor = conn.cursor()
    
    for group_jid, project in GROUPS.items():
        print(f"\n📱 {project.upper()} GROUP:")
        
        cursor.execute("""
            SELECT sender, content, timestamp, filename 
            FROM messages 
            WHERE chat_jid = ? AND media_type = 'image'
            ORDER BY timestamp DESC 
            LIMIT 5
        """, (group_jid,))
        
        messages = cursor.fetchall()
        if not messages:
            print("   No image messages found")
            continue
        
        for i, (sender, content, timestamp, filename) in enumerate(messages):
            print(f"   {i+1}. From: {sender}")
            print(f"      Content: '{content or 'No caption'}'")
            
            # Test parsing
            parsed = parse_message(content or "")
            if parsed:
                step_name = QA_STEPS.get(parsed['qa_step'], 'Unknown')
                print(f"      ✅ Valid: {parsed['drop_number']} Step {parsed['qa_step']} ({step_name})")
            else:
                print("      ❌ Invalid: Missing drop number or step")
            print()
    
    conn.close()
    return True

def main():
    print("🧪 Simple Upload Test")
    print("=" * 30)
    
    # Run tests
    db_ok = test_database()
    test_message_parsing()
    
    if db_ok:
        test_recent_messages()
    
    print("\n🚀 Test complete!")
    if db_ok:
        print("Ready to run: python simple_upload.py")
    else:
        print("Fix database connection first")

if __name__ == "__main__":
    main()