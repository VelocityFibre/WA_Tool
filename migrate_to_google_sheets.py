#!/usr/bin/env python3
"""
Migrate WhatsApp Velo Chat Data to Google Sheets
===============================================

This script migrates WhatsApp messages and chat data from the SQLite database 
to the "Velo Test" sheet in Google Sheets, mirroring the functionality of 
migrate_to_neon.py but targeting Google Sheets instead.
"""

import os
import sqlite3
from datetime import datetime
import sys
import logging
from typing import List, Dict, Any

# Google Sheets imports
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("❌ Google Sheets libraries not available. Install with:")
    print("pip install google-api-python-client google-auth")
    sys.exit(1)

# Configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GSHEET_ID = os.getenv("GSHEET_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Path to the WhatsApp messages database
MESSAGES_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               'whatsapp-mcp/whatsapp-bridge/store/messages.db')

# Sheet names for different data types
CHATS_SHEET = "Velo_Chats"
MESSAGES_SHEET = "Velo_Messages"
DROPS_SHEET = "Velo Test"  # Main sheet for drop data

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('velo_sheets_migration.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    if not GSHEET_ID:
        raise EnvironmentError("GSHEET_ID environment variable not set")
    
    if not GOOGLE_APPLICATION_CREDENTIALS:
        raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        raise FileNotFoundError(f"Credentials file not found: {GOOGLE_APPLICATION_CREDENTIALS}")

def connect_to_whatsapp_db():
    """Connect to the WhatsApp SQLite database"""
    if not os.path.exists(MESSAGES_DB_PATH):
        raise FileNotFoundError(f"WhatsApp database not found at: {MESSAGES_DB_PATH}")
    
    conn = sqlite3.connect(MESSAGES_DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def get_sheets_service():
    """Get Google Sheets service connection"""
    credentials = Credentials.from_service_account_file(
        GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES
    )
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)

def format_timestamp_for_sheets(timestamp_ms):
    """Format timestamp from milliseconds to readable date string"""
    try:
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "Unknown"

def create_sheet_if_not_exists(service, sheet_name: str):
    """Create a new sheet tab if it doesn't exist"""
    try:
        # Get existing sheet metadata
        spreadsheet = service.spreadsheets().get(spreadsheetId=GSHEET_ID).execute()
        existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
        
        if sheet_name not in existing_sheets:
            # Create new sheet
            request = {
                'addSheet': {
                    'properties': {
                        'title': sheet_name,
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 26
                        }
                    }
                }
            }
            
            service.spreadsheets().batchUpdate(
                spreadsheetId=GSHEET_ID,
                body={'requests': [request]}
            ).execute()
            
            logging.info(f"Created new sheet: {sheet_name}")
        else:
            logging.info(f"Sheet already exists: {sheet_name}")
            
    except Exception as e:
        logging.error(f"Error creating sheet {sheet_name}: {e}")
        raise

def setup_chats_sheet_headers(service):
    """Setup headers for the Velo_Chats sheet"""
    headers = [
        "JID",
        "Name", 
        "Last Message Time",
        "Total Messages",
        "Last Updated"
    ]
    
    service.spreadsheets().values().update(
        spreadsheetId=GSHEET_ID,
        range=f"{CHATS_SHEET}!A1:E1",
        valueInputOption="USER_ENTERED",
        body={"values": [headers]}
    ).execute()
    
    logging.info(f"Set up headers for {CHATS_SHEET}")

def setup_messages_sheet_headers(service):
    """Setup headers for the Velo_Messages sheet"""
    headers = [
        "Message ID",
        "Chat JID",
        "Chat Name",
        "Sender",
        "Content",
        "Timestamp",
        "Is From Me",
        "Media Type",
        "Filename",
        "URL",
        "File Length"
    ]
    
    service.spreadsheets().values().update(
        spreadsheetId=GSHEET_ID,
        range=f"{MESSAGES_SHEET}!A1:K1",
        valueInputOption="USER_ENTERED",
        body={"values": [headers]}
    ).execute()
    
    logging.info(f"Set up headers for {MESSAGES_SHEET}")

def migrate_chats_to_sheets(service, sqlite_conn):
    """Migrate chats data to Google Sheets"""
    cursor = sqlite_conn.cursor()
    
    # Get chats data
    cursor.execute("SELECT jid, name, last_message_time FROM chats")
    chats = cursor.fetchall()
    
    if not chats:
        logging.info("No chats found to migrate")
        return
    
    logging.info(f"Migrating {len(chats)} chats to Google Sheets...")
    
    # Prepare data for batch insert
    rows_data = []
    for chat in chats:
        chat_dict = dict(chat)
        
        # Count messages for this chat
        cursor.execute("SELECT COUNT(*) FROM messages WHERE chat_jid = ?", (chat_dict['jid'],))
        message_count = cursor.fetchone()[0]
        
        # Format timestamp
        last_message_time = "Unknown"
        if chat_dict.get('last_message_time'):
            last_message_time = format_timestamp_for_sheets(chat_dict['last_message_time'])
        
        row = [
            chat_dict['jid'],
            chat_dict['name'],
            last_message_time,
            message_count,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        rows_data.append(row)
    
    # Clear existing data (except headers)
    service.spreadsheets().values().clear(
        spreadsheetId=GSHEET_ID,
        range=f"{CHATS_SHEET}!A2:E"
    ).execute()
    
    # Insert all chat data
    service.spreadsheets().values().append(
        spreadsheetId=GSHEET_ID,
        range=f"{CHATS_SHEET}!A2:E",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": rows_data}
    ).execute()
    
    logging.info(f"Successfully migrated {len(chats)} chats to Google Sheets")

def migrate_messages_to_sheets(service, sqlite_conn, limit: int = 1000):
    """Migrate recent messages data to Google Sheets"""
    cursor = sqlite_conn.cursor()
    
    # Get recent messages with chat names
    query = """
        SELECT m.id, m.chat_jid, c.name as chat_name, m.sender, m.content, 
               m.timestamp, m.is_from_me, m.media_type, m.filename, m.url, m.file_length
        FROM messages m
        LEFT JOIN chats c ON m.chat_jid = c.jid
        ORDER BY m.timestamp DESC
        LIMIT ?
    """
    
    cursor.execute(query, (limit,))
    messages = cursor.fetchall()
    
    if not messages:
        logging.info("No messages found to migrate")
        return
    
    logging.info(f"Migrating {len(messages)} most recent messages to Google Sheets...")
    
    # Prepare data for batch insert
    rows_data = []
    for message in messages:
        msg_dict = dict(message)
        
        # Format timestamp
        timestamp = "Unknown"
        if msg_dict.get('timestamp'):
            timestamp = format_timestamp_for_sheets(msg_dict['timestamp'])
        
        # Clean content for sheets (remove newlines, limit length)
        content = str(msg_dict.get('content', ''))[:500].replace('\n', ' ').replace('\r', '')
        
        row = [
            msg_dict['id'],
            msg_dict['chat_jid'],
            msg_dict.get('chat_name', 'Unknown'),
            msg_dict.get('sender', ''),
            content,
            timestamp,
            "Yes" if msg_dict.get('is_from_me') else "No",
            msg_dict.get('media_type', ''),
            msg_dict.get('filename', ''),
            msg_dict.get('url', ''),
            msg_dict.get('file_length', 0)
        ]
        rows_data.append(row)
    
    # Clear existing data (except headers)
    service.spreadsheets().values().clear(
        spreadsheetId=GSHEET_ID,
        range=f"{MESSAGES_SHEET}!A2:K"
    ).execute()
    
    # Insert message data in batches
    batch_size = 100
    for i in range(0, len(rows_data), batch_size):
        batch = rows_data[i:i+batch_size]
        
        service.spreadsheets().values().append(
            spreadsheetId=GSHEET_ID,
            range=f"{MESSAGES_SHEET}!A2:K",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": batch}
        ).execute()
        
        logging.info(f"Migrated batch {i//batch_size + 1}/{(len(rows_data)-1)//batch_size + 1}")
    
    logging.info(f"Successfully migrated {len(messages)} messages to Google Sheets")

def identify_velo_drops_from_messages(service, sqlite_conn):
    """Identify potential Velo drop numbers from messages and add to Velo Test sheet"""
    cursor = sqlite_conn.cursor()
    
    # Look for messages that might contain drop numbers
    # This is a simplified version - you may need to adjust the pattern
    query = """
        SELECT m.id, m.chat_jid, c.name as chat_name, m.sender, m.content, m.timestamp
        FROM messages m
        LEFT JOIN chats c ON m.chat_jid = c.jid
        WHERE (LOWER(m.content) LIKE '%velo%' OR LOWER(m.content) LIKE '%drop%')
        AND m.content IS NOT NULL
        ORDER BY m.timestamp DESC
        LIMIT 50
    """
    
    cursor.execute(query)
    potential_drops = cursor.fetchall()
    
    if not potential_drops:
        logging.info("No potential Velo drops found in messages")
        return
    
    logging.info(f"Found {len(potential_drops)} potential Velo drop messages")
    
    # Prepare sample drop data for Velo Test sheet
    rows_data = []
    for drop_msg in potential_drops:
        msg_dict = dict(drop_msg)
        
        # Extract potential drop number (simplified)
        content = str(msg_dict.get('content', ''))
        
        # Create a test drop entry
        timestamp = format_timestamp_for_sheets(msg_dict['timestamp'])
        user_name = str(msg_dict.get('sender', 'Unknown'))[:20]
        
        # Extract drop number from content (very basic - you may need to improve this)
        drop_number = f"VELO_{msg_dict['id'][:8]}"  # Use message ID as fallback
        
        comment = f"Auto-migrated from WhatsApp message: {content[:100]}..."
        
        # Row data matching Velo Test sheet structure
        row = [
            timestamp.split(' ')[0],  # A: Date (just date part)
            drop_number,              # B: Drop Number
            False, False, False, False, False, False, False,  # C-I: Steps 1-7
            False, False, False, False, False, False, False,  # J-P: Steps 8-14
            0,                        # Q: Completed Photos
            14,                       # R: Outstanding Photos
            user_name,                # S: User
            "No",                     # T: 1MAP Loaded
            comment                   # U: Comment
        ]
        rows_data.append(row)
    
    if rows_data:
        # Add to Velo Test sheet
        service.spreadsheets().values().append(
            spreadsheetId=GSHEET_ID,
            range=f"{DROPS_SHEET}!A:U",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": rows_data}
        ).execute()
        
        logging.info(f"Added {len(rows_data)} potential drops to Velo Test sheet")

def migrate_velo_data_to_sheets():
    """Main migration function"""
    logger = setup_logging()
    
    try:
        # Check environment
        check_environment()
        logger.info("Environment check passed")
        
        # Connect to databases
        sqlite_conn = connect_to_whatsapp_db()
        logger.info("Connected to WhatsApp SQLite database")
        
        service = get_sheets_service()
        logger.info("Connected to Google Sheets")
        
        # Create sheets if they don't exist
        create_sheet_if_not_exists(service, CHATS_SHEET)
        create_sheet_if_not_exists(service, MESSAGES_SHEET)
        
        # Setup sheet headers
        setup_chats_sheet_headers(service)
        setup_messages_sheet_headers(service)
        
        # Migrate data
        migrate_chats_to_sheets(service, sqlite_conn)
        migrate_messages_to_sheets(service, sqlite_conn, limit=1000)
        identify_velo_drops_from_messages(service, sqlite_conn)
        
        logger.info("✅ Migration completed successfully!")
        logger.info(f"📊 Check your Google Sheet: https://docs.google.com/spreadsheets/d/{GSHEET_ID}/edit")
        
        # Close connections
        sqlite_conn.close()
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    print("🔄 Starting Velo WhatsApp data migration to Google Sheets...")
    print("=" * 60)
    migrate_velo_data_to_sheets()