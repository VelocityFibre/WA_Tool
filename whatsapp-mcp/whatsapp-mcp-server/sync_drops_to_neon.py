#!/usr/bin/env python3
"""
Script to sync WhatsApp drop numbers to Neon PostgreSQL database.
Usage: uv run python sync_drops_to_neon.py [--days N] [--today] [--dry-run]
"""

import argparse
import re
import psycopg2
from datetime import datetime, timedelta
from whatsapp import list_messages
from urllib.parse import urlparse
import os

# Database connection string
NEON_DB_URL = "postgresql://neondb_owner:npg_RIgDxzo4St6d@ep-damp-credit-a857vku0-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"

# Project configurations
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
    },
    'Mohadin': {
        'group_jid': '120363421532174586@g.us',
        'project_name': 'Mohadin',
        'group_description': 'Mohadin Activations group'
    }
}

# Legacy variables for backward compatibility
LAWLEY_GROUP_JID = PROJECTS['Lawley']['group_jid']

def get_whatsapp_drop_numbers(days=7, today_only=False, project_filter=None):
    """Extract drop numbers from WhatsApp for all or specific projects."""
    projects_to_check = [project_filter] if project_filter else list(PROJECTS.keys())
    print(f"🔍 Extracting drop numbers from {', '.join(projects_to_check)} project(s)...")
    
    # Set date filter
    if today_only:
        after_date = datetime.now().date().isoformat()
        print(f"   Filter: Today only ({after_date})")
    else:
        after_date = (datetime.now() - timedelta(days=days)).isoformat()
        print(f"   Filter: Last {days} days (since {after_date})")
    
    # Extract drop numbers from all specified projects
    drop_pattern = r'DR\d+'
    found_drops = {}
    
    for project_name in projects_to_check:
        if project_name not in PROJECTS:
            continue
            
        project_config = PROJECTS[project_name]
        group_jid = project_config['group_jid']
        
        print(f"   Processing {project_name} project ({project_config['group_description']})...")
        
        # Get messages containing DR for this project
        messages = list_messages(
            chat_jid=group_jid, 
            query='DR', 
            after=after_date, 
            limit=200
        )
        
        message_lines = messages.split('\n')
        
        for line in message_lines:
            drops_in_line = re.findall(drop_pattern, line, re.IGNORECASE)
            
            for drop in drops_in_line:
                drop_upper = drop.upper()
                
                # Extract timestamp and sender info
                timestamp_match = re.search(r'\[([\d\-\s:]+)\]', line)
                sender_match = re.search(r'From:\s*([^:]+):', line)
                
                timestamp = timestamp_match.group(1) if timestamp_match else 'Unknown time'
                sender = sender_match.group(1) if sender_match else 'Unknown sender'
                
                # Project-specific address
                address = f'Extracted from WhatsApp {project_config["group_description"]}'
                
                # Keep the latest occurrence of each drop number (with project info)
                drop_key = f"{drop_upper}-{project_name}"  # Ensure unique keys per project
                if drop_key not in found_drops or timestamp > found_drops[drop_key]['timestamp']:
                    found_drops[drop_key] = {
                        'drop_number': drop_upper,
                        'timestamp': timestamp,
                        'sender': sender,
                        'contractor_name': f'WhatsApp-{sender[:20]}...' if len(sender) > 20 else f'WhatsApp-{sender}',
                        'address': address,
                        'project_name': project_name
                    }
    
    return list(found_drops.values())

def connect_to_database():
    """Connect to Neon PostgreSQL database."""
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def get_existing_drop_numbers(conn):
    """Get existing drop numbers from database."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT drop_number FROM installations WHERE drop_number LIKE 'DR%'")
        existing = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return existing
    except Exception as e:
        print(f"❌ Error fetching existing drop numbers: {e}")
        return []

def insert_drop_numbers(conn, drop_data, dry_run=False):
    """Insert new drop numbers into the database."""
    try:
        cursor = conn.cursor()
        
        # Get existing DR drop numbers
        existing_drops = get_existing_drop_numbers(conn)
        print(f"📊 Found {len(existing_drops)} existing DR drop numbers in database")
        
        new_drops = []
        skipped_drops = []
        
        for drop_info in drop_data:
            drop_number = drop_info['drop_number']
            
            if drop_number in existing_drops:
                skipped_drops.append(drop_number)
                continue
                
            new_drops.append(drop_info)
        
        print(f"📝 New drops to insert: {len(new_drops)}")
        print(f"⏭️  Skipped (already exists): {len(skipped_drops)}")
        
        if skipped_drops:
            print(f"   Skipped: {', '.join(skipped_drops)}")
        
        if not new_drops:
            print("✅ No new drop numbers to insert.")
            cursor.close()
            return True
        
        if dry_run:
            print("\n🔍 DRY RUN - Would insert these drop numbers:")
            for drop_info in new_drops:
                print(f"   • {drop_info['drop_number']} from {drop_info['contractor_name']}")
            cursor.close()
            return True
        
        # Insert new drops
        insert_query = """
        INSERT INTO installations (
            drop_number, 
            contractor_name, 
            address, 
            status, 
            agent_notes,
            project_name
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        inserted_count = 0
        for drop_info in new_drops:
            try:
                cursor.execute(insert_query, (
                    drop_info['drop_number'],
                    drop_info['contractor_name'],
                    drop_info['address'],
                    'submitted',
                    f"Auto-imported from WhatsApp on {datetime.now().isoformat()} - Original timestamp: {drop_info['timestamp']}",
                    drop_info.get('project_name', 'Unknown')
                ))
                inserted_count += 1
                print(f"✅ Inserted: {drop_info['drop_number']}")
                
            except Exception as e:
                print(f"❌ Error inserting {drop_info['drop_number']}: {e}")
        
        conn.commit()
        cursor.close()
        
        print(f"\n🎉 Successfully inserted {inserted_count} new drop numbers!")
        return True
        
    except Exception as e:
        print(f"❌ Error during insertion: {e}")
        if conn:
            conn.rollback()
        return False

def sync_drops_to_database(days=7, today_only=False, dry_run=False):
    """Main function to sync WhatsApp drops to database."""
    print("🚀 Starting WhatsApp to Neon DB sync...")
    print(f"{'📋 DRY RUN MODE' if dry_run else '💾 LIVE MODE'}")
    print("=" * 60)
    
    # Get drop numbers from WhatsApp
    whatsapp_drops = get_whatsapp_drop_numbers(days, today_only)
    
    if not whatsapp_drops:
        print("❌ No drop numbers found in WhatsApp messages.")
        return False
    
    print(f"📱 Found {len(whatsapp_drops)} drop numbers from WhatsApp:")
    for drop in whatsapp_drops:
        print(f"   • {drop['drop_number']} - {drop['timestamp']}")
    
    print("\n" + "=" * 60)
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return False
    
    print("✅ Connected to Neon database")
    
    # Insert drop numbers
    success = insert_drop_numbers(conn, whatsapp_drops, dry_run)
    
    conn.close()
    print("🔐 Database connection closed")
    
    return success

def main():
    parser = argparse.ArgumentParser(description='Sync WhatsApp drop numbers to Neon database')
    parser.add_argument('--days', type=int, default=7, 
                       help='Number of days to look back (default: 7)')
    parser.add_argument('--today', action='store_true', 
                       help='Only sync today\'s drop numbers')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview what would be inserted without making changes')
    
    args = parser.parse_args()
    
    success = sync_drops_to_database(
        days=args.days, 
        today_only=args.today,
        dry_run=args.dry_run
    )
    
    if success:
        print("\n✅ Sync completed successfully!")
    else:
        print("\n❌ Sync failed!")
        exit(1)

if __name__ == "__main__":
    main()