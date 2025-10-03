#!/usr/bin/env python3
"""
Update existing qa_photo_reviews records with correct project information
based on WhatsApp message origins.

This script will:
1. Find all qa_photo_reviews records with project = NULL
2. Look up the original WhatsApp messages for each drop number
3. Determine the project based on the chat group
4. Update the project column with the correct value
"""

import psycopg2
import sqlite3
from datetime import datetime
import re

# Configuration
NEON_DB_URL = "postgresql://neondb_owner:npg_RIgDxzo4St6d@ep-damp-credit-a857vku0-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
MESSAGES_DB_PATH = '../whatsapp-bridge/store/messages.db'

# Project configurations (same as realtime_drop_monitor.py)
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

DROP_PATTERN = r'DR\d+'

def get_records_with_null_project():
    """Get all qa_photo_reviews records where project is NULL."""
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, drop_number, review_date 
            FROM qa_photo_reviews 
            WHERE project IS NULL
            ORDER BY id
        """)
        
        records = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return records
    except Exception as e:
        print(f"❌ Error fetching NULL project records: {e}")
        return []

def find_project_for_drop_number(drop_number):
    """Find which project a drop number belongs to by searching WhatsApp messages."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        # Search for the drop number in messages
        cursor.execute("""
            SELECT chat_jid, content, timestamp 
            FROM messages 
            WHERE content LIKE ? 
            ORDER BY timestamp DESC
        """, (f'%{drop_number}%',))
        
        messages = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not messages:
            print(f"   ⚠️  No WhatsApp messages found for {drop_number}")
            return None
        
        # Check which project the chat belongs to
        for chat_jid, content, timestamp in messages:
            # Verify the drop number is actually in this message
            if re.search(DROP_PATTERN, content, re.IGNORECASE):
                found_drops = re.findall(DROP_PATTERN, content, re.IGNORECASE)
                if drop_number.upper() in [d.upper() for d in found_drops]:
                    # Find which project this chat belongs to
                    for project_name, config in PROJECTS.items():
                        if chat_jid == config['group_jid']:
                            print(f"   ✅ {drop_number} → {project_name} (from {chat_jid})")
                            return project_name
        
        print(f"   ❓ {drop_number} found in messages but no matching project group")
        return None
        
    except Exception as e:
        print(f"   ❌ Error searching for {drop_number}: {e}")
        return None

def update_project_for_record(record_id, drop_number, project_name, dry_run=False):
    """Update the project column for a specific record."""
    if dry_run:
        print(f"   🔍 DRY RUN: Would update {drop_number} → project = '{project_name}'")
        return True
    
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE qa_photo_reviews 
            SET project = %s 
            WHERE id = %s
        """, (project_name, record_id))
        
        rows_updated = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        
        if rows_updated > 0:
            print(f"   ✅ Updated {drop_number} → project = '{project_name}'")
            return True
        else:
            print(f"   ⚠️  No rows updated for {drop_number}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error updating {drop_number}: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Update existing QA photo reviews with correct project information')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without making updates')
    
    args = parser.parse_args()
    
    print("🚀 Starting project update for existing QA photo reviews...")
    print(f"{'📋 DRY RUN MODE' if args.dry_run else '💾 LIVE MODE'}")
    print("=" * 60)
    
    # Get records with NULL project
    null_records = get_records_with_null_project()
    
    if not null_records:
        print("✅ No records found with NULL project. All records already have project assignments!")
        return
    
    print(f"📊 Found {len(null_records)} records with NULL project")
    print("\n🔍 Analyzing each record...")
    
    # Track statistics
    updated_count = 0
    lawley_count = 0
    velo_count = 0
    unknown_count = 0
    
    for record_id, drop_number, review_date in null_records:
        print(f"\n🔍 Processing {drop_number} (ID: {record_id})...")
        
        # Find which project this drop belongs to
        project_name = find_project_for_drop_number(drop_number)
        
        if project_name:
            if update_project_for_record(record_id, drop_number, project_name, args.dry_run):
                updated_count += 1
                if project_name == 'Lawley':
                    lawley_count += 1
                elif project_name == 'Velo Test':
                    velo_count += 1
        else:
            unknown_count += 1
            print(f"   ❓ Could not determine project for {drop_number}")
    
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print(f"   Total records processed: {len(null_records)}")
    print(f"   Successfully updated: {updated_count}")
    print(f"   → Lawley: {lawley_count}")
    print(f"   → Velo Test: {velo_count}")
    print(f"   Unknown/Unmatched: {unknown_count}")
    
    if args.dry_run:
        print("\n🔍 This was a dry run. Use --live to apply the changes.")
    else:
        print(f"\n✅ Update complete! {updated_count} records updated.")

if __name__ == "__main__":
    main()