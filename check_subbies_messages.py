#!/usr/bin/env python3
import os
import sqlite3
import sys
from datetime import datetime

# Path to the WhatsApp messages database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                      'whatsapp-mcp/whatsapp-bridge/store/messages.db')

# VF subbies group JID from extract_daily_update.py
SUBBIES_GROUP_JID = '120363417538730975@g.us'

def check_database_exists():
    """Check if the WhatsApp database exists"""
    if not os.path.exists(DB_PATH):
        print(f"WhatsApp database not found at: {DB_PATH}")
        return False
    return True

def get_chat_info():
    """Get information about the subbies group chat"""
    if not check_database_exists():
        return
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get chat information
        cursor.execute("SELECT jid, name FROM chats WHERE jid = ?", (SUBBIES_GROUP_JID,))
        chat = cursor.fetchone()
        
        if not chat:
            print(f"No chat found with JID: {SUBBIES_GROUP_JID}")
            
            # Try to find any group chats that might be the subbies group
            cursor.execute("SELECT jid, name FROM chats WHERE jid LIKE '%@g.us'")
            group_chats = cursor.fetchall()
            
            if group_chats:
                print(f"\nFound {len(group_chats)} group chats:")
                for i, (jid, name) in enumerate(group_chats):
                    print(f"{i+1}. JID: {jid}, Name: {name}")
            else:
                print("No group chats found in the database.")
        else:
            print(f"Found subbies group chat: {chat[1]} (JID: {chat[0]})")
            return chat[0]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

def check_messages(jid=None):
    """Check messages in the subbies group chat"""
    if not check_database_exists():
        return
    
    if not jid:
        jid = SUBBIES_GROUP_JID
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if the messages table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'")
        if not cursor.fetchone():
            print("Messages table not found in the database.")
            return
        
        # Get column names
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Message table columns: {columns}")
        
        # Check for messages with media
        try:
            cursor.execute("""
                SELECT id, timestamp, fromMe, sender, content, type
                FROM messages
                WHERE chat_jid = ? AND type IN ('image', 'video', 'document')
                ORDER BY timestamp DESC
                LIMIT 20
            """, (jid,))
        except sqlite3.OperationalError:
            # If the above fails, try with a different schema
            try:
                cursor.execute("""
                    SELECT id, timestamp, sender, content, type
                    FROM messages
                    WHERE chat_jid = ? AND type IN ('image', 'video', 'document')
                    ORDER BY timestamp DESC
                    LIMIT 20
                """, (jid,))
            except sqlite3.OperationalError:
                # If that also fails, try a more generic approach
                cursor.execute(f"SELECT * FROM messages WHERE chat_jid = ? LIMIT 20", (jid,))
        
        media_messages = cursor.fetchall()
        
        if not media_messages:
            print(f"No media messages found in the subbies group chat.")
            
            # Check if there are any messages at all
            cursor.execute("""
                SELECT COUNT(*) FROM messages WHERE chat_jid = ?
            """, (jid,))
            
            count = cursor.fetchone()[0]
            print(f"Total messages in this chat: {count}")
            
            if count > 0:
                # Get the most recent messages
                cursor.execute("""
                    SELECT id, timestamp, type, content
                    FROM messages
                    WHERE chat_jid = ?
                    ORDER BY timestamp DESC
                    LIMIT 5
                """, (jid,))
                
                recent_messages = cursor.fetchall()
                print("\nMost recent messages:")
                for msg in recent_messages:
                    msg_dict = dict(zip(['id', 'timestamp', 'type', 'content'], msg))
                    timestamp = datetime.fromtimestamp(msg_dict['timestamp'] / 1000)
                    print(f"[{timestamp}] [{msg_dict['type']}] {msg_dict['content'][:100]}...")
        else:
            print(f"\nFound {len(media_messages)} media messages in the subbies group chat:")
            
            # Display media messages
            for i, msg in enumerate(media_messages):
                msg_dict = dict(zip(columns[:len(msg)], msg))
                
                # Format timestamp
                timestamp_ms = msg_dict.get('timestamp', 0)
                timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                
                # Get message type and content
                msg_type = msg_dict.get('type', 'unknown')
                content = msg_dict.get('content', '')
                
                print(f"{i+1}. [{timestamp}] Type: {msg_type}, ID: {msg_dict.get('id', 'N/A')}")
                if content:
                    print(f"   Content: {content[:100]}...")
                print()
    
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Checking VF Subbies WhatsApp Group Messages\n")
    
    # Get chat info
    chat_jid = get_chat_info()
    
    # Check messages
    if chat_jid:
        check_messages(chat_jid)
    else:
        print("\nTrying with the default JID...")
        check_messages()
