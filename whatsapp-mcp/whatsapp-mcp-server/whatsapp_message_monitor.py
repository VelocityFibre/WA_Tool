#!/usr/bin/env python3
"""
WhatsApp Message Monitor - Watches for QA resubmissions
=======================================================

Monitors WhatsApp messages in the Velo Test group for "resubmitted" keywords
and automatically updates the Google Sheet to mark items as resubmitted.
"""

import os
import time
import logging
import sys
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse

# Google Sheets imports
try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    print("❌ Google Sheets libraries not available. Install with:")
    print("uv add google-api-python-client google-auth")
    sys.exit(1)

# Import WhatsApp functionality
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whatsapp

# Initialize logger at module level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('whatsapp_message_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GSHEET_ID = os.getenv("GSHEET_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
SHEET_NAME = "Velo Test"

# WhatsApp Group JID for Velo Test
VELO_TEST_GROUP_JID = "120363421664266245@g.us"

def get_sheets_service():
    """Get Google Sheets service connection"""
    try:
        credentials = Credentials.from_service_account_file(
            GOOGLE_APPLICATION_CREDENTIALS, scopes=SCOPES
        )
        return build("sheets", "v4", credentials=credentials, cache_discovery=False)
    except Exception as e:
        logger.error(f"Failed to create Google Sheets service: {e}")
        return None

def get_recent_whatsapp_messages(hours_back: int = 1) -> List[whatsapp.Message]:
    """Get recent WhatsApp messages from Velo Test group"""
    try:
        import sqlite3
        
        since_time = datetime.now() - timedelta(hours=hours_back)
        
        conn = sqlite3.connect(whatsapp.MESSAGES_DB_PATH)
        cursor = conn.cursor()
        
        # Query messages directly from database
        cursor.execute("""
            SELECT messages.timestamp, messages.sender, chats.name, messages.content, 
                   messages.is_from_me, chats.jid, messages.id, messages.media_type
            FROM messages
            JOIN chats ON messages.chat_jid = chats.jid
            WHERE messages.chat_jid = ? AND messages.timestamp > ?
            ORDER BY messages.timestamp DESC
            LIMIT 50
        """, (VELO_TEST_GROUP_JID, since_time))
        
        results = cursor.fetchall()
        
        messages = []
        for msg in results:
            message = whatsapp.Message(
                timestamp=datetime.fromisoformat(msg[0]),
                sender=msg[1],
                chat_name=msg[2],
                content=msg[3],
                is_from_me=msg[4],
                chat_jid=msg[5],
                id=msg[6],
                media_type=msg[7]
            )
            messages.append(message)
        
        cursor.close()
        conn.close()
        
        return messages
        
    except Exception as e:
        logger.error(f"Error getting WhatsApp messages: {e}")
        return []

def extract_drop_number_from_message(content: str) -> Optional[str]:
    """Extract drop number from WhatsApp message content"""
    # Look for patterns like "DR0000002", "DR123456", etc.
    patterns = [
        r'\b(DR\d+)\b',  # DR followed by digits
        r'\b(dr\d+)\b',  # lowercase dr followed by digits
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).upper()  # Always return uppercase
    
    return None

def is_resubmission_message(content: str) -> bool:
    """Check if message indicates a resubmission"""
    resubmission_keywords = [
        'resubmitted', 'resubmit', 're-submitted', 're-submit',
        'submitted', 'submit', 'updated', 'fixed', 'completed photos',
        'photos updated', 'done', 'ready for review', 'update'
    ]
    
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in resubmission_keywords)

def get_sheet_row_by_drop_number(drop_number: str) -> Optional[Dict]:
    """Find the row in Google Sheet that contains the specified drop number"""
    try:
        service = get_sheets_service()
        if not service:
            return None
        
        # Get all data from the sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=GSHEET_ID,
            range=f"{SHEET_NAME}!A:Z"
        ).execute()
        
        values = result.get('values', [])
        
        for row_index, row in enumerate(values):
            if len(row) > 1 and row[1].strip().upper() == drop_number:
                return {
                    'row_number': row_index + 1,  # 1-based for sheets API
                    'data': row
                }
        
        return None
        
    except Exception as e:
        logger.error(f"Error searching sheet for drop {drop_number}: {e}")
        return None

def update_sheet_for_resubmission(drop_number: str, resubmission_time: datetime) -> bool:
    """Update Google Sheet to tick Resubmitted checkbox"""
    try:
        service = get_sheets_service()
        if not service:
            return False
        
        # Find the row
        row_info = get_sheet_row_by_drop_number(drop_number)
        if not row_info:
            logger.warning(f"Drop {drop_number} not found in sheet")
            return False
        
        row_number = row_info['row_number']
        
        # Just tick the Resubmitted checkbox (Column W)
        service.spreadsheets().values().update(
            spreadsheetId=GSHEET_ID,
            range=f"{SHEET_NAME}!W{row_number}",
            valueInputOption='RAW',
            body={'values': [['TRUE']]}
        ).execute()
        
        logger.info(f"✅ Ticked Resubmitted checkbox for {drop_number}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating sheet for {drop_number}: {e}")
        return False

def ensure_sheet_headers() -> bool:
    """Ensure the sheet has the required headers for our new columns"""
    try:
        service = get_sheets_service()
        if not service:
            return False
        
        # Check if headers exist and add if needed
        result = service.spreadsheets().values().get(
            spreadsheetId=GSHEET_ID,
            range=f"{SHEET_NAME}!W1:Y1"
        ).execute()
        
        current_headers = result.get('values', [[]])[0] if result.get('values') else []
        
        # Add headers if they don't exist
        headers_to_add = []
        if len(current_headers) < 1 or current_headers[0] != "Resubmitted":
            headers_to_add.append("Resubmitted")
        if len(current_headers) < 2 or (len(current_headers) > 1 and current_headers[1] != "Resubmission Time"):
            headers_to_add.append("Resubmission Time")
        if len(current_headers) < 3 or (len(current_headers) > 2 and current_headers[2] != "Completed"):
            headers_to_add.append("Completed")
        
        if headers_to_add:
            # Update headers
            start_col = chr(87 + len(current_headers))  # W, X, Y, etc.
            end_col = chr(87 + len(current_headers) + len(headers_to_add) - 1)
            
            service.spreadsheets().values().update(
                spreadsheetId=GSHEET_ID,
                range=f"{SHEET_NAME}!{start_col}1:{end_col}1",
                valueInputOption='RAW',
                body={'values': [headers_to_add]}
            ).execute()
            
            logger.info(f"✅ Added headers: {', '.join(headers_to_add)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating sheet headers: {e}")
        return False

def process_resubmission_messages(dry_run: bool = False) -> int:
    """Process recent WhatsApp messages for resubmissions"""
    messages = get_recent_whatsapp_messages()
    resubmissions_processed = 0
    
    if not messages:
        logger.debug("No recent WhatsApp messages found")
        return 0
    
    logger.info(f"📱 Checking {len(messages)} recent messages for resubmissions...")
    
    for message in messages:
        # Skip our own messages
        if message.is_from_me:
            continue
            
        # Check if message indicates resubmission
        if not is_resubmission_message(message.content):
            continue
            
        # Extract drop number
        drop_number = extract_drop_number_from_message(message.content)
        if not drop_number:
            logger.debug(f"No drop number found in message: {message.content[:50]}...")
            continue
        
        logger.info(f"🔍 Found resubmission message: {drop_number} from {whatsapp.get_sender_name(message.sender)}")
        logger.info(f"   Message: {message.content}")
        
        if dry_run:
            logger.info(f"🔍 DRY RUN: Would mark {drop_number} as resubmitted")
        else:
            # Update the sheet
            if update_sheet_for_resubmission(drop_number, message.timestamp):
                resubmissions_processed += 1
                logger.info(f"✅ Processed resubmission for {drop_number}")
            else:
                logger.error(f"❌ Failed to process resubmission for {drop_number}")
    
    return resubmissions_processed

def monitor_whatsapp_messages(dry_run: bool = False, check_interval: int = 30):
    """Main monitoring loop for WhatsApp messages"""
    
    logger.info("🚀 Starting WhatsApp Message Monitor...")
    logger.info(f"{'📋 DRY RUN MODE' if dry_run else '💾 LIVE MODE'}")
    logger.info(f"⏰ Check interval: {check_interval} seconds")
    logger.info(f"📱 Monitoring group: Velo Test")
    logger.info(f"🔍 Looking for: resubmission messages with drop numbers")
    logger.info("=" * 70)
    
    # Ensure headers exist
    ensure_sheet_headers()
    
    while True:
        try:
            processed = process_resubmission_messages(dry_run)
            
            if processed > 0:
                logger.info(f"📊 Processed {processed} resubmissions")
            else:
                logger.debug("📊 No resubmissions found")
            
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("⚠️  Received keyboard interrupt. Shutting down...")
            break
        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
            logger.info(f"⏰ Waiting {check_interval} seconds before retry...")
            time.sleep(check_interval)
    
    logger.info("🛑 WhatsApp Message Monitor stopped")

def main():
    parser = argparse.ArgumentParser(description='WhatsApp Message Monitor for QA Resubmissions')
    parser.add_argument('--dry-run', action='store_true', help='Preview mode - don\'t actually update sheet')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds (default: 30)')
    parser.add_argument('--test', action='store_true', help='Run single test check and exit')
    
    args = parser.parse_args()
    
    try:
        if args.test:
            logger.info("🧪 Running single test check...")
            processed = process_resubmission_messages(args.dry_run)
            logger.info(f"✅ Test completed - processed {processed} resubmissions")
            return
            
        # Start monitoring
        monitor_whatsapp_messages(args.dry_run, args.interval)
        
    except KeyboardInterrupt:
        logger.info("⚠️  Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()