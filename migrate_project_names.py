#!/usr/bin/env python3
"""
Migration script to populate project_name column for existing chats
based on their WhatsApp group JIDs.
"""

import sqlite3
import os

# Project configurations (copied from realtime_drop_monitor.py)
PROJECTS = {
    'Lawley': {
        'group_jid': '120363418298130331@g.us',
        'project_name': 'Lawley',
        'group_description': 'Lawley Activation 3 group'
    },
    'Velo Test': {
        'group_jid': '120363421664266245@g.us', 
        'project_name': 'Velo Test',
        'group_description': 'Velo Test group'
    }
}

# Path to the WhatsApp messages database
MESSAGES_DB_PATH = './whatsapp-mcp/whatsapp-bridge/store/messages.db'

def migrate_project_names():
    """Update existing chats with project names based on their JIDs."""
    
    if not os.path.exists(MESSAGES_DB_PATH):
        print(f"❌ Database not found at: {MESSAGES_DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        # Get current chats
        cursor.execute("SELECT jid, name FROM chats")
        existing_chats = cursor.fetchall()
        
        print(f"📊 Found {len(existing_chats)} existing chats")
        
        updated_count = 0
        
        # Create JID to project name mapping
        jid_to_project = {}
        for project_name, config in PROJECTS.items():
            jid_to_project[config['group_jid']] = project_name
        
        # Update each chat with appropriate project name
        for jid, name in existing_chats:
            project_name = jid_to_project.get(jid)
            
            if project_name:
                cursor.execute(
                    "UPDATE chats SET project_name = ? WHERE jid = ?",
                    (project_name, jid)
                )
                updated_count += 1
                print(f"✅ Updated {name or jid} -> {project_name}")
            else:
                # For non-project groups, set to null or 'General'
                cursor.execute(
                    "UPDATE chats SET project_name = ? WHERE jid = ?",
                    ('General', jid)
                )
                print(f"ℹ️  Updated {name or jid} -> General")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"\n🎉 Migration complete! Updated {updated_count} project-specific chats.")
        print(f"📋 Project mapping:")
        for project_name, config in PROJECTS.items():
            print(f"   • {project_name}: {config['group_jid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def verify_migration():
    """Verify the migration was successful."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT project_name, COUNT(*) FROM chats GROUP BY project_name")
        results = cursor.fetchall()
        
        print(f"\n📊 Chat distribution by project:")
        for project_name, count in results:
            print(f"   • {project_name or 'NULL'}: {count} chats")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting project name migration...")
    
    if migrate_project_names():
        verify_migration()
    else:
        print("❌ Migration failed")
        exit(1)