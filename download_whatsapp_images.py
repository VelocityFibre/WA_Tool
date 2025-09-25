#!/usr/bin/env python3
"""
Script to download images from the Velocity Fibre subbies WhatsApp group
and organize them by date in the specified directory structure.
"""
import os
import sys
import json
import shutil
import requests
import sqlite3
from datetime import datetime
from pathlib import Path

# Constants
SUBBIES_GROUP_JID = '120363417538730975@g.us'  # Velocity/fibretime subbies group JID
WHATSAPP_API_URL = 'http://localhost:8080/api'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                      'whatsapp-mcp/whatsapp-bridge/store/messages.db')
BASE_MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media/images')

def setup_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs(BASE_MEDIA_DIR, exist_ok=True)
    print(f"Media directory set up at: {BASE_MEDIA_DIR}")

def get_image_messages(days=30, limit=100):
    """
    Get image messages from the WhatsApp database
    
    Args:
        days: Number of days to look back
        limit: Maximum number of messages to retrieve
        
    Returns:
        List of image message dictionaries
    """
    try:
        # Try using the WhatsApp API first
        response = requests.post(
            f"{WHATSAPP_API_URL}/list-messages",
            json={
                "chat_jid": SUBBIES_GROUP_JID,
                "limit": limit,
                "include_context": False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'messages' in data:
                # Filter for image messages
                image_messages = []
                for msg in data['messages']:
                    if msg.get('type') == 'image':
                        image_messages.append(msg)
                
                print(f"Found {len(image_messages)} image messages via WhatsApp API")
                return image_messages
            else:
                print("No messages found in API response")
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"Error using WhatsApp API: {str(e)}")
        print("Falling back to direct database access...")
    
    # Fallback to direct database access
    try:
        if not os.path.exists(DB_PATH):
            print(f"WhatsApp database not found at: {DB_PATH}")
            return []
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get column names to understand the schema
        cursor.execute("PRAGMA table_info(messages)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Check if there's a type or mimetype column
        if 'type' in columns:
            cursor.execute("""
                SELECT id, timestamp, sender, content, type
                FROM messages
                WHERE chat_jid = ? AND type = 'image'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (SUBBIES_GROUP_JID, limit))
        elif 'mimetype' in columns:
            cursor.execute("""
                SELECT id, timestamp, sender, content, mimetype
                FROM messages
                WHERE chat_jid = ? AND mimetype LIKE 'image/%'
                ORDER BY timestamp DESC
                LIMIT ?
            """, (SUBBIES_GROUP_JID, limit))
        elif 'data' in columns:
            # If there's a data column, it might contain JSON with type information
            cursor.execute("""
                SELECT id, timestamp, sender, content, data
                FROM messages
                WHERE chat_jid = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (SUBBIES_GROUP_JID, limit * 5))  # Get more messages since we'll filter later
        else:
            print("Could not find a suitable column to identify image messages")
            return []
        
        messages = cursor.fetchall()
        conn.close()
        
        if not messages:
            print("No messages found in the database")
            return []
        
        # Process messages to identify images
        image_messages = []
        for msg in messages:
            msg_dict = dict(zip(columns[:len(msg)], msg))
            
            # Check if this is an image message
            is_image = False
            if 'type' in msg_dict and msg_dict['type'] == 'image':
                is_image = True
            elif 'mimetype' in msg_dict and msg_dict['mimetype'] and msg_dict['mimetype'].startswith('image/'):
                is_image = True
            elif 'data' in msg_dict and msg_dict['data']:
                try:
                    data = json.loads(msg_dict['data'])
                    if data.get('type') == 'image' or (isinstance(data, dict) and data.get('mimetype', '').startswith('image/')):
                        is_image = True
                except:
                    pass
            
            if is_image:
                image_messages.append({
                    'id': msg_dict['id'],
                    'timestamp': msg_dict['timestamp'],
                    'sender': msg_dict.get('sender', ''),
                    'content': msg_dict.get('content', '')
                })
        
        print(f"Found {len(image_messages)} image messages via database")
        return image_messages
    
    except Exception as e:
        print(f"Error accessing database: {str(e)}")
        return []

def download_image(message_id, chat_jid=SUBBIES_GROUP_JID):
    """
    Download an image using the WhatsApp API
    
    Args:
        message_id: ID of the message containing the image
        chat_jid: JID of the chat containing the message
        
    Returns:
        Path to the downloaded image or None if download failed
    """
    try:
        # Try using the WhatsApp API
        response = requests.post(
            f"{WHATSAPP_API_URL}/download",
            json={
                "message_id": message_id,
                "chat_jid": chat_jid
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'file_path' in data:
                return data['file_path']
            else:
                print(f"Download failed: {data.get('message', 'Unknown error')}")
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"Error downloading image: {str(e)}")
    
    return None

def organize_image(source_path, message_id, timestamp):
    """
    Organize an image into the date-based directory structure
    
    Args:
        source_path: Path to the downloaded image
        message_id: ID of the message containing the image
        timestamp: Timestamp of the message in milliseconds
        
    Returns:
        Path to the organized image or None if organization failed
    """
    try:
        # Convert timestamp to datetime
        dt = datetime.fromtimestamp(timestamp / 1000)
        date_str = dt.strftime('%Y-%m-%d')
        time_str = dt.strftime('%H%M%S')
        
        # Create date directory if it doesn't exist
        date_dir = os.path.join(BASE_MEDIA_DIR, date_str)
        os.makedirs(date_dir, exist_ok=True)
        
        # Determine file extension
        _, ext = os.path.splitext(source_path)
        if not ext:
            ext = '.jpg'  # Default to .jpg if no extension
        
        # Create target path
        target_filename = f"image_{time_str}_{message_id}{ext}"
        target_path = os.path.join(date_dir, target_filename)
        
        # Copy the file
        shutil.copy2(source_path, target_path)
        print(f"Copied image to: {target_path}")
        
        return target_path
    
    except Exception as e:
        print(f"Error organizing image: {str(e)}")
        return None

def main():
    """Main function to download and organize WhatsApp images"""
    print("Starting WhatsApp image download and organization")
    
    # Set up directories
    setup_directories()
    
    # Get image messages
    image_messages = get_image_messages()
    
    if not image_messages:
        print("No image messages found to download")
        return
    
    print(f"Downloading {len(image_messages)} images...")
    
    # Download and organize each image
    successful_downloads = 0
    for msg in image_messages:
        message_id = msg['id']
        timestamp = msg['timestamp']
        
        print(f"Processing image message: {message_id}")
        
        # Download the image
        source_path = download_image(message_id)
        if not source_path:
            print(f"Failed to download image for message: {message_id}")
            continue
        
        # Organize the image
        target_path = organize_image(source_path, message_id, timestamp)
        if target_path:
            successful_downloads += 1
    
    print(f"Successfully downloaded and organized {successful_downloads} out of {len(image_messages)} images")

if __name__ == "__main__":
    main()
