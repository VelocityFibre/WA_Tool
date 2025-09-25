#!/usr/bin/env python3
import os
import sqlite3
import psycopg2
from datetime import datetime
import sys

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
    """Format timestamp from milliseconds to PostgreSQL timestamp"""
    try:
        # Convert milliseconds to seconds and create datetime
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.isoformat()
    except:
        return None

def create_neon_tables(pg_conn):
    """Create tables in Neon PostgreSQL database"""
    cursor = pg_conn.cursor()
    
    # Create chats table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS whatsapp_chats (
        jid TEXT PRIMARY KEY,
        name TEXT,
        last_message_time TIMESTAMP
    );
    """)
    
    # Create messages table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS whatsapp_messages (
        id TEXT,
        chat_jid TEXT,
        sender TEXT,
        content TEXT,
        timestamp TIMESTAMP,
        is_from_me BOOLEAN,
        media_type TEXT,
        filename TEXT,
        url TEXT,
        file_length INTEGER,
        PRIMARY KEY (id, chat_jid),
        FOREIGN KEY (chat_jid) REFERENCES whatsapp_chats(jid)
    );
    """)
    
    pg_conn.commit()
    print("Created tables in Neon PostgreSQL database")

def migrate_to_neon(neon_connection_string):
    """Migrate WhatsApp data to Neon PostgreSQL"""
    # Step 1: Connect to WhatsApp database
    sqlite_conn = connect_to_whatsapp_db()
    sqlite_cursor = sqlite_conn.cursor()
    
    # Step 2: Connect to Neon PostgreSQL
    try:
        pg_conn = psycopg2.connect(neon_connection_string)
        print("Connected to Neon PostgreSQL database")
    except Exception as e:
        print(f"Error connecting to Neon PostgreSQL: {e}")
        return
    
    # Step 3: Create tables in Neon
    create_neon_tables(pg_conn)
    pg_cursor = pg_conn.cursor()
    
    # Step 4: Migrate chats data
    sqlite_cursor.execute("SELECT jid, name, last_message_time FROM chats")
    chats = sqlite_cursor.fetchall()
    
    print(f"Migrating {len(chats)} chats...")
    for chat in chats:
        chat_dict = dict(chat)
        
        # Format timestamp if it exists
        last_message_time = None
        if chat_dict.get('last_message_time'):
            last_message_time = format_timestamp(chat_dict['last_message_time'])
        
        # Insert into Neon PostgreSQL
        try:
            pg_cursor.execute("""
            INSERT INTO whatsapp_chats (jid, name, last_message_time)
            VALUES (%s, %s, %s)
            ON CONFLICT (jid) DO UPDATE 
            SET name = EXCLUDED.name, 
                last_message_time = EXCLUDED.last_message_time
            """, (
                chat_dict['jid'],
                chat_dict['name'],
                last_message_time
            ))
        except Exception as e:
            print(f"Error inserting chat {chat_dict['jid']}: {e}")
    
    pg_conn.commit()
    print("Chats migration completed")
    
    # Step 5: Migrate messages data
    sqlite_cursor.execute("""
        SELECT id, chat_jid, sender, content, timestamp, is_from_me, 
               media_type, filename, url, file_length
        FROM messages
        ORDER BY timestamp DESC
    """)
    messages = sqlite_cursor.fetchall()
    
    print(f"Migrating {len(messages)} messages...")
    batch_size = 100
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i+batch_size]
        for message in batch:
            msg_dict = dict(message)
            
            # Format timestamp
            timestamp = None
            if msg_dict.get('timestamp'):
                timestamp = format_timestamp(msg_dict['timestamp'])
            
            # Insert into Neon PostgreSQL
            try:
                pg_cursor.execute("""
                INSERT INTO whatsapp_messages 
                (id, chat_jid, sender, content, timestamp, is_from_me, 
                media_type, filename, url, file_length)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id, chat_jid) DO UPDATE 
                SET sender = EXCLUDED.sender,
                    content = EXCLUDED.content,
                    timestamp = EXCLUDED.timestamp,
                    is_from_me = EXCLUDED.is_from_me,
                    media_type = EXCLUDED.media_type,
                    filename = EXCLUDED.filename,
                    url = EXCLUDED.url,
                    file_length = EXCLUDED.file_length
                """, (
                    msg_dict['id'],
                    msg_dict['chat_jid'],
                    msg_dict.get('sender'),
                    msg_dict.get('content'),
                    timestamp,
                    bool(msg_dict.get('is_from_me')),
                    msg_dict.get('media_type'),
                    msg_dict.get('filename'),
                    msg_dict.get('url'),
                    msg_dict.get('file_length')
                ))
            except Exception as e:
                print(f"Error inserting message {msg_dict['id']}: {e}")
        
        pg_conn.commit()
        print(f"Migrated batch {i//batch_size + 1}/{(len(messages)-1)//batch_size + 1}")
    
    print("Messages migration completed successfully!")
    
    # Close connections
    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate_to_neon.py <neon_connection_string>")
        print("Example: python migrate_to_neon.py 'postgresql://user:password@ep-xyz-123.us-east-2.aws.neon.tech/neondb'")
        sys.exit(1)
    
    neon_connection_string = sys.argv[1]
    migrate_to_neon(neon_connection_string)
