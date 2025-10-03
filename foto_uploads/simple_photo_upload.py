#!/usr/bin/env python3
"""
Step 1: Simple Photo Upload from WhatsApp Groups
Basic photo detection, download, and storage without AI processing
"""

import os
import sys
import sqlite3
import psycopg2
import requests
import json
import hashlib
from datetime import datetime
from pathlib import Path
import logging

# Configuration
BASE_DIR = Path(__file__).parent
WHATSAPP_DB_PATH = BASE_DIR.parent / 'whatsapp-mcp/whatsapp-bridge/store/messages.db'
PHOTOS_STORAGE_PATH = BASE_DIR / 'photos'
WHATSAPP_BRIDGE_URL = 'http://localhost:8080'

# Database configuration
NEON_DB_URL = os.getenv('NEON_DATABASE_URL', '')

# Test group configuration (start with existing groups for testing)
TEST_GROUPS = {
    '120363418298130331@g.us': {
        'name': 'Lawley Activation 3',
        'project_code': 'LAW',
        'enabled': True
    },
    '120363421664266245@g.us': {
        'name': 'Velo Test', 
        'project_code': 'VEL',
        'enabled': True
    }
}

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(BASE_DIR / 'photo_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SimplePhotoUpload:
    """Simple photo upload service - Step 1 implementation"""
    
    def __init__(self):
        self.setup_directories()
        self.setup_database()
        
    def setup_directories(self):
        """Create necessary directories"""
        PHOTOS_STORAGE_PATH.mkdir(exist_ok=True)
        
        # Create project directories
        for group_jid, config in TEST_GROUPS.items():
            project_dir = PHOTOS_STORAGE_PATH / config['project_code'].lower()
            project_dir.mkdir(exist_ok=True)
            
            # Create subdirectories
            (project_dir / 'incoming').mkdir(exist_ok=True)
            (project_dir / 'processed').mkdir(exist_ok=True)
            
        logger.info(f"Directories set up at: {PHOTOS_STORAGE_PATH}")
    
    def setup_database(self):
        """Create basic database table for photo uploads"""
        if not NEON_DB_URL:
            logger.warning("NEON_DATABASE_URL not set, using SQLite fallback")
            return
            
        try:
            conn = psycopg2.connect(NEON_DB_URL)
            cursor = conn.cursor()
            
            # Create simple photo uploads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simple_photo_uploads (
                    id SERIAL PRIMARY KEY,
                    message_id TEXT NOT NULL,
                    chat_jid TEXT NOT NULL,
                    group_name TEXT,
                    project_code TEXT,
                    sender_phone TEXT,
                    message_content TEXT,
                    original_filename TEXT,
                    stored_filename TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    upload_timestamp TIMESTAMP DEFAULT NOW(),
                    processed BOOLEAN DEFAULT FALSE,
                    UNIQUE(message_id, chat_jid)
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Database table created/verified")
            
        except Exception as e:
            logger.error(f"Database setup error: {e}")
    
    def connect_to_whatsapp_db(self):
        """Connect to WhatsApp SQLite database"""
        if not WHATSAPP_DB_PATH.exists():
            raise FileNotFoundError(f"WhatsApp database not found at: {WHATSAPP_DB_PATH}")
        
        conn = sqlite3.connect(str(WHATSAPP_DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn
    
    def download_photo_from_whatsapp(self, message_id, chat_jid):
        """Download photo using WhatsApp bridge API"""
        try:
            download_url = f"{WHATSAPP_BRIDGE_URL}/api/download"
            payload = {
                'message_id': message_id,
                'chat_jid': chat_jid
            }
            
            response = requests.post(download_url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('path')
                else:
                    logger.error(f"Download failed: {result.get('message')}")
            else:
                logger.error(f"HTTP {response.status_code}: {response.text}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading photo {message_id}: {e}")
            return None
    
    def organize_photo(self, source_path, message_info):
        """Organize photo into project structure"""
        try:
            if not os.path.exists(source_path):
                logger.error(f"Source file not found: {source_path}")
                return None
            
            project_code = message_info['project_code'].lower()
            project_dir = PHOTOS_STORAGE_PATH / project_code / 'processed'
            
            # Create date-based subdirectory
            date_str = datetime.now().strftime('%Y-%m-%d')
            date_dir = project_dir / date_str
            date_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            original_name = message_info.get('original_filename', 'photo.jpg')
            name, ext = os.path.splitext(original_name)
            timestamp = datetime.now().strftime('%H%M%S')
            new_filename = f"{message_info['message_id'][:8]}_{timestamp}{ext}"
            
            target_path = date_dir / new_filename
            
            # Copy file
            import shutil
            shutil.copy2(source_path, target_path)
            
            logger.info(f"Photo organized: {target_path}")
            return str(target_path)
            
        except Exception as e:
            logger.error(f"Error organizing photo: {e}")
            return None
    
    def store_photo_metadata(self, photo_info):
        """Store photo metadata in database"""
        if not NEON_DB_URL:
            logger.info("No database configured, skipping metadata storage")
            return True
            
        try:
            conn = psycopg2.connect(NEON_DB_URL)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO simple_photo_uploads (
                    message_id, chat_jid, group_name, project_code, 
                    sender_phone, message_content, original_filename,
                    stored_filename, file_path, file_size, processed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id, chat_jid) DO NOTHING
            """, (
                photo_info['message_id'],
                photo_info['chat_jid'],
                photo_info['group_name'],
                photo_info['project_code'],
                photo_info['sender_phone'],
                photo_info['message_content'],
                photo_info['original_filename'],
                photo_info['stored_filename'],
                photo_info['file_path'],
                photo_info['file_size'],
                True  # processed
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Metadata stored for {photo_info['message_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing metadata: {e}")
            return False
    
    def extract_drop_number(self, content):
        """Extract drop number from message content"""
        if not content:
            return None
        
        import re
        pattern = r'\bDR\d+\b'
        matches = re.findall(pattern, content.upper())
        return matches[0] if matches else None
    
    def get_new_photos(self):
        """Get new photo messages from monitored groups"""
        try:
            wa_conn = self.connect_to_whatsapp_db()
            cursor = wa_conn.cursor()
            
            new_photos = []
            
            # Check each monitored group
            for group_jid, config in TEST_GROUPS.items():
                if not config.get('enabled', True):
                    continue
                
                # Get recent image messages (last 24 hours)
                cutoff_timestamp = int((datetime.now().timestamp() - 86400) * 1000)
                
                cursor.execute("""
                    SELECT id, chat_jid, sender, content, timestamp, 
                           filename, url, file_length, media_type
                    FROM messages 
                    WHERE chat_jid = ? 
                    AND media_type = 'image' 
                    AND timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT 20
                """, (group_jid, cutoff_timestamp))
                
                messages = cursor.fetchall()
                
                for msg in messages:
                    msg_dict = dict(msg)
                    
                    photo_info = {
                        'message_id': msg_dict['id'],
                        'chat_jid': group_jid,
                        'group_name': config['name'],
                        'project_code': config['project_code'],
                        'sender_phone': msg_dict.get('sender', ''),
                        'message_content': msg_dict.get('content', ''),
                        'original_filename': msg_dict.get('filename', 'photo.jpg'),
                        'file_size': msg_dict.get('file_length', 0),
                        'timestamp': msg_dict.get('timestamp', 0),
                        'drop_number': self.extract_drop_number(msg_dict.get('content'))
                    }
                    
                    new_photos.append(photo_info)
            
            wa_conn.close()
            return new_photos
            
        except Exception as e:
            logger.error(f"Error getting new photos: {e}")
            return []
    
    def process_photos(self):
        """Main processing function - download and organize new photos"""
        logger.info("Starting photo processing...")
        
        # Get new photos from WhatsApp
        new_photos = self.get_new_photos()
        
        if not new_photos:
            logger.info("No new photos found")
            return 0
        
        logger.info(f"Found {len(new_photos)} new photos to process")
        
        successful_count = 0
        
        for photo_info in new_photos:
            try:
                logger.info(f"Processing photo: {photo_info['message_id']} from {photo_info['group_name']}")
                
                # Download photo from WhatsApp
                downloaded_path = self.download_photo_from_whatsapp(
                    photo_info['message_id'], 
                    photo_info['chat_jid']
                )
                
                if not downloaded_path:
                    logger.warning(f"Failed to download photo: {photo_info['message_id']}")
                    continue
                
                # Organize photo into project structure
                organized_path = self.organize_photo(downloaded_path, photo_info)
                
                if not organized_path:
                    logger.warning(f"Failed to organize photo: {photo_info['message_id']}")
                    continue
                
                # Update photo info with final paths
                photo_info['file_path'] = organized_path
                photo_info['stored_filename'] = os.path.basename(organized_path)
                
                # Store metadata in database
                if self.store_photo_metadata(photo_info):
                    successful_count += 1
                    
                    # Log success with details
                    details = []
                    if photo_info['drop_number']:
                        details.append(f"Drop: {photo_info['drop_number']}")
                    if photo_info['sender_phone']:
                        details.append(f"From: {photo_info['sender_phone']}")
                    
                    logger.info(f"✅ Photo processed successfully: {photo_info['stored_filename']} " + 
                              (f"({', '.join(details)})" if details else ""))
                else:
                    logger.warning(f"Photo organized but metadata storage failed: {photo_info['message_id']}")
                
            except Exception as e:
                logger.error(f"Error processing photo {photo_info.get('message_id', 'unknown')}: {e}")
        
        logger.info(f"Photo processing complete: {successful_count}/{len(new_photos)} successful")
        return successful_count
    
    def run_once(self):
        """Run processing once and exit"""
        try:
            count = self.process_photos()
            print(f"Processed {count} photos")
            return count
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return 0
    
    def run_continuous(self, interval_seconds=60):
        """Run processing continuously"""
        logger.info(f"Starting continuous photo monitoring (interval: {interval_seconds}s)")
        
        import time
        while True:
            try:
                count = self.process_photos()
                if count > 0:
                    logger.info(f"Processed {count} photos")
                
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Service stopped by user")
                break
            except Exception as e:
                logger.error(f"Service error: {e}")
                time.sleep(interval_seconds)

def main():
    """Main function"""
    print("🔧 Simple Photo Upload Service - Step 1")
    print("======================================")
    
    service = SimplePhotoUpload()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            print("Running once...")
            count = service.run_once()
            print(f"✅ Complete: {count} photos processed")
        elif sys.argv[1] == '--continuous':
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
            print(f"Running continuously (interval: {interval}s)...")
            service.run_continuous(interval)
        else:
            print("Usage: python simple_photo_upload.py [--once|--continuous [interval]]")
    else:
        print("Running once by default...")
        count = service.run_once()
        print(f"✅ Complete: {count} photos processed")

if __name__ == "__main__":
    main()