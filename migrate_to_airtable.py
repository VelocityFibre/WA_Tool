#!/usr/bin/env python3
import os
import sqlite3
import json
from datetime import datetime

# Airtable MCP functions
from mcp0_list_bases import mcp0_list_bases
from mcp0_create_table import mcp0_create_table
from mcp0_create_record import mcp0_create_record

# Path to the WhatsApp messages database
MESSAGES_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               'whatsapp-mcp/whatsapp-bridge/store/messages.db')

def connect_to_whatsapp_db():
    """Connect to the WhatsApp SQLite database"""
    if not os.path.exists(MESSAGES_DB_PATH):
        raise FileNotFoundError(f"WhatsApp database not found at: {MESSAGES_DB_PATH}")
    
    conn = sqlite3.connect(MESSAGES_DB_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    return conn

def format_timestamp(timestamp_ms):
    """Format timestamp from milliseconds to ISO format"""
    try:
        # Convert milliseconds to seconds and create datetime
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.isoformat()
    except:
        return str(timestamp_ms)

def migrate_to_airtable():
    """Migrate WhatsApp data to Airtable"""
    # Step 1: Connect to WhatsApp database
    conn = connect_to_whatsapp_db()
    cursor = conn.cursor()
    
    # Step 2: List Airtable bases to get the base_id
    bases_response = mcp0_list_bases()
    
    if not bases_response.get('bases'):
        print("No Airtable bases found. Please create one first.")
        return
    
    # Ask user to select a base or create a new one
    print("Available Airtable bases:")
    for i, base in enumerate(bases_response['bases']):
        print(f"{i+1}. {base['name']} (ID: {base['id']})")
    
    base_choice = input("Enter the number of the base to use, or 'new' to create a new one: ")
    
    if base_choice.lower() == 'new':
        base_name = input("Enter a name for the new base: ")
        # Note: Creating a new base via API requires a paid Airtable account
        # This would need to be done manually in the Airtable interface
        print("Please create a new base in Airtable and run this script again.")
        return
    else:
        try:
            base_index = int(base_choice) - 1
            base_id = bases_response['bases'][base_index]['id']
        except (ValueError, IndexError):
            print("Invalid selection. Please try again.")
            return
    
    # Step 3: Create tables in Airtable
    
    # Create Chats table
    chats_table_response = mcp0_create_table(
        base_id=base_id,
        table_name="WhatsApp Chats",
        description="WhatsApp chat contacts",
        fields=[
            {"name": "JID", "type": "singleLineText"},
            {"name": "Name", "type": "singleLineText"},
            {"name": "Last Message Time", "type": "dateTime"}
        ]
    )
    
    # Create Messages table
    messages_table_response = mcp0_create_table(
        base_id=base_id,
        table_name="WhatsApp Messages",
        description="WhatsApp messages",
        fields=[
            {"name": "Message ID", "type": "singleLineText"},
            {"name": "Chat JID", "type": "singleLineText"},
            {"name": "Sender", "type": "singleLineText"},
            {"name": "Content", "type": "multilineText"},
            {"name": "Timestamp", "type": "dateTime"},
            {"name": "Is From Me", "type": "checkbox"},
            {"name": "Media Type", "type": "singleLineText"},
            {"name": "Filename", "type": "singleLineText"},
            {"name": "URL", "type": "url"},
            {"name": "File Length", "type": "number"}
        ]
    )
    
    # Step 4: Migrate chats data
    cursor.execute("SELECT jid, name, last_message_time FROM chats")
    chats = cursor.fetchall()
    
    print(f"Migrating {len(chats)} chats...")
    for chat in chats:
        chat_dict = dict(chat)
        
        # Format timestamp if it exists
        if chat_dict.get('last_message_time'):
            chat_dict['last_message_time'] = format_timestamp(chat_dict['last_message_time'])
        
        # Create record in Airtable
        mcp0_create_record(
            base_id=base_id,
            table_name="WhatsApp Chats",
            fields={
                "JID": chat_dict['jid'],
                "Name": chat_dict['name'] or "",
                "Last Message Time": chat_dict.get('last_message_time', "")
            }
        )
    
    # Step 5: Migrate messages data
    cursor.execute("""
        SELECT id, chat_jid, sender, content, timestamp, is_from_me, 
               media_type, filename, url, file_length
        FROM messages
        ORDER BY timestamp DESC
        LIMIT 1000  # Adjust this limit as needed
    """)
    messages = cursor.fetchall()
    
    print(f"Migrating {len(messages)} messages...")
    for message in messages:
        msg_dict = dict(message)
        
        # Format timestamp
        if msg_dict.get('timestamp'):
            msg_dict['timestamp'] = format_timestamp(msg_dict['timestamp'])
        
        # Create record in Airtable
        mcp0_create_record(
            base_id=base_id,
            table_name="WhatsApp Messages",
            fields={
                "Message ID": msg_dict['id'],
                "Chat JID": msg_dict['chat_jid'],
                "Sender": msg_dict.get('sender', ""),
                "Content": msg_dict.get('content', ""),
                "Timestamp": msg_dict.get('timestamp', ""),
                "Is From Me": bool(msg_dict.get('is_from_me')),
                "Media Type": msg_dict.get('media_type', ""),
                "Filename": msg_dict.get('filename', ""),
                "URL": msg_dict.get('url', ""),
                "File Length": msg_dict.get('file_length', 0)
            }
        )
    
    print("Migration to Airtable completed successfully!")
    conn.close()

if __name__ == "__main__":
    migrate_to_airtable()
