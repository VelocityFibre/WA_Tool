#!/usr/bin/env python3
"""
Find Mohadin WhatsApp Group JID
This script helps identify the WhatsApp group JID for Mohadin project
"""

import sqlite3
import sys
import os

# Add whatsapp module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def find_mohadin_groups():
    """Find WhatsApp groups that might be the Mohadin group"""
    
    messages_db_path = '../whatsapp-bridge/store/messages.db'
    
    if not os.path.exists(messages_db_path):
        print("❌ WhatsApp database not found!")
        print(f"Expected: {messages_db_path}")
        return
    
    try:
        conn = sqlite3.connect(messages_db_path)
        cursor = conn.cursor()
        
        # Get all group chats
        cursor.execute("""
            SELECT jid, name, project_name 
            FROM chats 
            WHERE jid LIKE '%@g.us'
            ORDER BY name
        """)
        
        groups = cursor.fetchall()
        
        print("🔍 Available WhatsApp Groups:")
        print("=" * 60)
        
        mohadin_candidates = []
        
        for jid, name, project_name in groups:
            print(f"📱 {name or 'Unnamed Group'}")
            print(f"   JID: {jid}")
            print(f"   Project: {project_name or 'None'}")
            
            # Look for Mohadin-related keywords
            if name and any(keyword.lower() in name.lower() 
                          for keyword in ['mohadin', 'moha', 'activation']):
                mohadin_candidates.append((jid, name, project_name))
                print("   🎯 POTENTIAL MOHADIN GROUP!")
            
            print()
        
        if mohadin_candidates:
            print("🎯 Mohadin Group Candidates Found:")
            print("=" * 40)
            for jid, name, project_name in mohadin_candidates:
                print(f"Group: {name}")
                print(f"JID: {jid}")
                print()
        else:
            print("⚠️  No obvious Mohadin group found.")
            print("Please check group names manually or create the group.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading database: {e}")

if __name__ == "__main__":
    find_mohadin_groups()