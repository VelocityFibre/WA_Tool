#!/usr/bin/env python3
import os
import sqlite3
import sys
import json
from datetime import datetime

# Path to the WhatsApp messages database
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                      'whatsapp-mcp/whatsapp-bridge/store/messages.db')

# VF subbies group JID from extract_daily_update.py
SUBBIES_GROUP_JID = '120363417538730975@g.us'

def check_photos():
    """Check for photos/images in the VF subbies WhatsApp group"""
    # Check if the database exists
    if not os.path.exists(DB_PATH):
        print(f"WhatsApp database not found at: {DB_PATH}")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # First, verify the group exists
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
                
                # Use the first group chat as a fallback
                group_jid = group_chats[0][0]
                print(f"\nUsing group: {group_chats[0][1]} ({group_jid})")
            else:
                print("No group chats found in the database.")
                return
        else:
            print(f"Found subbies group chat: {chat[1]} (JID: {chat[0]})")
            group_jid = chat[0]
        
        # Get the table schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Database tables: {[t[0] for t in tables]}")
        
        # Get column names to understand the schema
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"Message columns: {columns}")
        
        # Check if the messages table has a data column (might contain JSON with message type)
        if 'data' in columns:
            print("Found 'data' column in messages table, checking for images...")
            
            # Query all messages from the group
            cursor.execute("""
                SELECT id, timestamp, data, content
                FROM messages
                WHERE chat_jid = ?
                ORDER BY timestamp DESC
                LIMIT 100
            """, (group_jid,))
            
            messages = cursor.fetchall()
            image_messages = []
            
            # Process each message to find images
            for msg in messages:
                msg_id, timestamp, data_str, content = msg
                
                # Try to parse the data column as JSON
                if data_str:
                    try:
                        data = json.loads(data_str)
                        msg_type = data.get('type')
                        
                        # Check if this is an image message
                        if msg_type == 'image' or (isinstance(data, dict) and data.get('mimetype', '').startswith('image/')):
                            image_messages.append({
                                'id': msg_id,
                                'timestamp': timestamp,
                                'content': content,
                                'data': data
                            })
                    except json.JSONDecodeError:
                        # Not JSON data, check if it contains image indicators
                        if 'image' in data_str.lower() or 'jpg' in data_str.lower() or 'png' in data_str.lower():
                            image_messages.append({
                                'id': msg_id,
                                'timestamp': timestamp,
                                'content': content,
                                'data': data_str[:100] + '...' if len(data_str) > 100 else data_str
                            })
            
            if image_messages:
                print(f"\nFound {len(image_messages)} potential image messages in the subbies group chat:")
                
                for i, msg in enumerate(image_messages):
                    # Format timestamp
                    timestamp_ms = msg['timestamp']
                    timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                    
                    print(f"{i+1}. [{timestamp}] Image ID: {msg['id']}")
                    if msg['content']:
                        print(f"   Caption: {msg['content']}")
                    print()
            else:
                print("No image messages found in the data column.")
                
        else:
            # Try different queries based on possible schema
            try:
                # First attempt: look for messages with mimetype starting with image/
                cursor.execute("""
                    SELECT id, timestamp, mimetype, content
                    FROM messages
                    WHERE chat_jid = ? AND mimetype LIKE 'image/%'
                    ORDER BY timestamp DESC
                    LIMIT 30
                """, (group_jid,))
            except sqlite3.OperationalError:
                try:
                    # Second attempt: look for a type column
                    cursor.execute("""
                        SELECT id, timestamp, content
                        FROM messages
                        WHERE chat_jid = ? AND type = 'image'
                        ORDER BY timestamp DESC
                        LIMIT 30
                    """, (group_jid,))
                except sqlite3.OperationalError:
                    # Last resort: get all messages and filter client-side
                    cursor.execute("""
                        SELECT id, timestamp, content
                        FROM messages
                        WHERE chat_jid = ?
                        ORDER BY timestamp DESC
                        LIMIT 100
                    """, (group_jid,))
        
        messages = cursor.fetchall()
        
        if not messages:
            print(f"No messages found in the subbies group chat using this query.")
            return
        
        # Try to identify image messages from the results
        image_messages = []
        
        # Create column map for the fetched messages
        col_map = {}
        if len(columns) >= len(messages[0]):
            col_map = {columns[i]: i for i in range(len(messages[0]))}
        
        # Process messages to find images
        for msg in messages:
            # Check if we have a mimetype column and it starts with image/
            if 'mimetype' in col_map and msg[col_map['mimetype']] and msg[col_map['mimetype']].startswith('image/'):
                image_messages.append(msg)
            # Check content for image indicators
            elif 'content' in col_map and msg[col_map['content']]:
                content = msg[col_map['content']]
                if '[IMAGE]' in content or 'image' in content.lower():
                    image_messages.append(msg)
        
        if not image_messages:
            print(f"No image messages identified in the subbies group chat.")
            return
        
        print(f"\nFound {len(image_messages)} potential image messages in the subbies group chat:")
        
        # Display image messages
        for i, msg in enumerate(image_messages):
            # Create a dictionary with column names as keys
            msg_dict = {}
            for j, val in enumerate(msg):
                if j < len(columns):
                    msg_dict[columns[j]] = val
                else:
                    msg_dict[f'col_{j}'] = val
            
            # Format timestamp
            timestamp_ms = msg_dict.get('timestamp', 0)
            timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
            
            # Get message ID and content
            msg_id = msg_dict.get('id', 'N/A')
            content = msg_dict.get('content', '')
            
            print(f"{i+1}. [{timestamp}] Image ID: {msg_id}")
            if content:
                print(f"   Caption: {content}")
            
            # Check if there's a media path
            if 'mediaPath' in msg_dict and msg_dict['mediaPath']:
                print(f"   Media Path: {msg_dict['mediaPath']}")
            
            print()
        
        # Provide instructions for downloading
        print("\nTo download an image, use the WhatsApp MCP tool with the message ID:")
        print("Example: mcp8_download_media(message_id=\"MESSAGE_ID\", chat_jid=\"" + group_jid + "\")")
        print("\nOr use the WhatsApp MCP directly:")
        print(f"mcp8_list_messages(chat_jid=\"{group_jid}\", query=\"image\", limit=20)")
        print("Then use mcp8_download_media with the message ID to download the image.")
        
        # Suggest using the WhatsApp MCP to list and download images
        print("\nFor a more direct approach, you can use the WhatsApp MCP tools to list and download images:")
        print("1. List messages with images in the group")
        print("2. Download specific images using their message IDs")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("Checking for Photos in VF Subbies WhatsApp Group\n")
    check_photos()
