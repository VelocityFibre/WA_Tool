#!/usr/bin/env python3
"""
Check if Mohadin group was detected after adding bridge number
"""

import sqlite3
import os
import time

def check_mohadin_group():
    """Check if Mohadin group appears in database"""
    
    messages_db_path = '../whatsapp-bridge/store/messages.db'
    
    if not os.path.exists(messages_db_path):
        print("❌ WhatsApp database not found!")
        return False
    
    try:
        conn = sqlite3.connect(messages_db_path)
        cursor = conn.cursor()
        
        # Search for Mohadin groups
        cursor.execute("""
            SELECT jid, name, project_name 
            FROM chats 
            WHERE name LIKE '%Mohadin%' OR name LIKE '%mohadin%'
            ORDER BY name
        """)
        
        mohadin_groups = cursor.fetchall()
        
        if mohadin_groups:
            print("🎉 MOHADIN GROUP DETECTED!")
            print("=" * 40)
            
            for jid, name, project_name in mohadin_groups:
                print(f"📱 Group: {name}")
                print(f"🆔 JID: {jid}")
                print(f"📋 Project: {project_name or 'None'}")
                print()
                
                # Auto-configure if found
                if jid and 'mohadin' in name.lower():
                    print(f"🔧 Ready to configure with JID: {jid}")
                    print(f"Run: ./add_mohadin_jid.sh \"{jid}\"")
                    print()
            
            cursor.close()
            conn.close()
            return True
        else:
            print("⏳ Mohadin group not yet detected.")
            print()
            print("Make sure:")
            print("  1. ✅ Bridge number +27 64 041 2391 is added to 'Mohadin Activations' group")
            print("  2. ✅ Post a test message in the group")
            print("  3. ✅ Wait 15 seconds for detection")
            print("  4. ✅ Run this script again")
            
            cursor.close()
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking for Mohadin Activations group...")
    print()
    
    if check_mohadin_group():
        print("✅ Ready to go live with Mohadin!")
    else:
        print("⏳ Waiting for Mohadin group detection...")