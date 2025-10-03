#!/usr/bin/env python3
"""
Enhanced QA Feedback System - WITH REPLY FUNCTIONALITY
======================================================

Key Features:
1. REPLY to sender instead of posting to group
2. GROUP TOGGLE FLAGS for easy enable/disable
3. TESTING MODE (only Velo Test enabled initially)

Date: October 2nd, 2025
"""

import os
import time
import logging
import sys
import sqlite3
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

import psycopg2
import whatsapp

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_qa_feedback.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
NEON_DB_URL = "postgresql://neondb_owner:npg_RIgDxzo4St6d@ep-damp-credit-a857vku0-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
WHATSAPP_BRIDGE_URL = "http://localhost:8080"
WHATSAPP_DB_PATH = os.getenv('WHATSAPP_DB_PATH', "../whatsapp-bridge/store/messages.db")

# GROUP CONFIGURATION WITH TOGGLE FLAGS
GROUP_CONFIG = {
    'Velo Test': {
        'group_jid': '120363421664266245@g.us',
        'group_name': 'Velo Test',
        'enabled': True,  # 🔥 ENABLED for testing
        'testing_mode': True  # Safe testing environment
    },
    'Mohadin': {
        'group_jid': '120363421532174586@g.us',
        'group_name': 'Mohadin Activations 🥳',
        'enabled': False,  # 🚫 DISABLED during testing
        'testing_mode': False
    },
    'Lawley': {
        'group_jid': '120363418298130331@g.us',
        'group_name': 'Lawley Activation 3',
        'enabled': False,  # 🚫 DISABLED during testing
        'testing_mode': False
    }
}

# Environment configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GSHEET_ID = os.getenv("GSHEET_ID", "1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")

# QA Steps for feedback
QA_STEPS = {
    'step_01_property_frontage': '1. Property Frontage Photo',
    'step_02_location_before_install': '2. Location Before Installation',
    'step_03_outside_cable_span': '3. Outside Cable Span',
    'step_04_home_entry_outside': '4. Home Entry Outside',
    'step_05_home_entry_inside': '5. Home Entry Inside',
    'step_06_fibre_entry_to_ont': '6. Fibre Entry to ONT',
    'step_07_patched_labelled_drop': '7. Patched & Labelled Drop',
    'step_08_work_area_completion': '8. Work Area Completion',
    'step_09_ont_barcode_scan': '9. ONT Barcode Scan',
    'step_10_ups_serial_number': '10. UPS Serial Number',
    'step_11_powermeter_reading': '11. Power Meter Reading',
    'step_12_powermeter_at_ont': '12. Power Meter at ONT',
    'step_13_active_broadband_light': '13. Active Broadband Light',
    'step_14_customer_signature': '14. Customer Signature'
}

def get_enabled_groups() -> Dict[str, Dict]:
    """Get only enabled groups for monitoring"""
    enabled = {name: config for name, config in GROUP_CONFIG.items() if config['enabled']}
    logger.info(f"📊 Active groups: {list(enabled.keys())}")
    return enabled

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

def get_drop_original_message(drop_number: str, group_jid: str) -> Optional[str]:
    """Find the original message ID where this drop number was posted"""
    try:
        # Connect to WhatsApp Bridge SQLite database
        whatsapp_db = os.path.abspath(WHATSAPP_DB_PATH)
        if not os.path.exists(whatsapp_db):
            logger.warning(f"WhatsApp database not found: {whatsapp_db}")
            return None
        
        conn = sqlite3.connect(whatsapp_db)
        cursor = conn.cursor()
        
        # Search for the drop number in messages
        cursor.execute("""
            SELECT id, content, sender, timestamp 
            FROM messages 
            WHERE chat_jid = ? 
            AND content LIKE ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (group_jid, f'%{drop_number}%'))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            message_id, content, sender, timestamp = result
            logger.info(f"📱 Found original message for {drop_number}: ID={message_id}, sender={sender}")
            return message_id
        else:
            logger.warning(f"⚠️ Original message not found for {drop_number} in {group_jid}")
            return None
            
    except Exception as e:
        logger.error(f"Error finding original message for {drop_number}: {e}")
        return None

def create_feedback_message(drop_number: str, missing_steps: List[str], project: str, assigned_agent: str) -> str:
    """Create a feedback message for missing QA steps"""
    
    message = f"""🔍 QA REVIEW INCOMPLETE - {drop_number}

The following photos/steps need to be updated in 1MAP:

"""
    
    # Add numbered list of missing steps
    for step in missing_steps:
        message += f"• {step}\n"
    
    message += f"""
📋 Project: {project}
👤 Assigned Agent: {assigned_agent or 'Not specified'}

Please update the missing photos in 1MAP and resubmit.
Once updated, the QA team will re-review the installation.

Thank you! 📸✅"""
    
    return message

def send_reply_to_sender(drop_number: str, group_jid: str, message: str, dry_run: bool = False) -> bool:
    """Send a REPLY to the original drop message sender"""
    
    if dry_run:
        logger.info(f"🔍 DRY RUN: Would reply to {drop_number} in {group_jid}")
        logger.info(f"Reply message: {message}")
        return True
    
    try:
        # Get the original message ID
        original_message_id = get_drop_original_message(drop_number, group_jid)
        
        if not original_message_id:
            # Fallback: send to group (old behavior)
            logger.warning(f"⚠️ Falling back to group message for {drop_number}")
            return send_group_message(group_jid, message, dry_run)
        
        # Send reply using WhatsApp Bridge API
        reply_payload = {
            "recipient": group_jid,
            "message": message,
            "reply_to": original_message_id  # This makes it a REPLY
        }
        
        success, response = whatsapp.send_message_reply(group_jid, message, original_message_id)
        
        if success:
            logger.info(f"✅ REPLY sent for {drop_number}")
            return True
        else:
            logger.error(f"❌ Failed to send reply for {drop_number}: {response}")
            # Fallback to group message
            return send_group_message(group_jid, message, dry_run)
            
    except Exception as e:
        logger.error(f"❌ Error sending reply for {drop_number}: {e}")
        # Fallback to group message
        return send_group_message(group_jid, message, dry_run)

def send_group_message(group_jid: str, message: str, dry_run: bool = False) -> bool:
    """Fallback: Send regular group message (old behavior)"""
    try:
        if dry_run:
            logger.info(f"🔍 DRY RUN: Would send group message to {group_jid}")
            return True
            
        success, response = whatsapp.send_message(group_jid, message)
        
        if success:
            logger.info(f"✅ Group message sent")
            return True
        else:
            logger.error(f"❌ Failed to send group message: {response}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error sending group message: {e}")
        return False

def get_sheet_data(sheet_name: str) -> List[List]:
    """Get data from specific Google Sheet"""
    try:
        service = get_sheets_service()
        if not service:
            return []
            
        result = service.spreadsheets().values().get(
            spreadsheetId=GSHEET_ID,
            range=f"{sheet_name}!A:X"
        ).execute()
        
        return result.get('values', [])
        
    except Exception as e:
        logger.error(f"Error reading {sheet_name} sheet: {e}")
        return []

def parse_sheet_row(row: List, row_number: int) -> Optional[Dict]:
    """Parse a sheet row into structured data"""
    try:
        # Ensure row has enough columns
        while len(row) < 24:
            row.append('')
        
        # Skip header rows and empty drop numbers
        if row_number <= 2 or not row[1].strip():
            return None
            
        drop_number = row[1].strip()
        if not drop_number.startswith('DR'):
            return None
            
        return {
            'row_number': row_number,
            'drop_number': drop_number,
            'qa_steps': {
                'step_01_property_frontage': row[2].lower() == 'true',
                'step_02_location_before_install': row[3].lower() == 'true',
                'step_03_outside_cable_span': row[4].lower() == 'true',
                'step_04_home_entry_outside': row[5].lower() == 'true',
                'step_05_home_entry_inside': row[6].lower() == 'true',
                'step_06_fibre_entry_to_ont': row[7].lower() == 'true',
                'step_07_patched_labelled_drop': row[8].lower() == 'true',
                'step_08_work_area_completion': row[9].lower() == 'true',
                'step_09_ont_barcode_scan': row[10].lower() == 'true',
                'step_10_ups_serial_number': row[11].lower() == 'true',
                'step_11_powermeter_reading': row[12].lower() == 'true',
                'step_12_powermeter_at_ont': row[13].lower() == 'true',
                'step_13_active_broadband_light': row[14].lower() == 'true',
                'step_14_customer_signature': row[15].lower() == 'true',
            },
            'user': row[18] if len(row) > 18 else '',
            'incomplete': row[21].lower() == 'true' if len(row) > 21 else False,
            'completed': row[23].lower() == 'true' if len(row) > 23 else False,
        }
        
    except Exception as e:
        logger.error(f"Error parsing row {row_number}: {e}")
        return None

def get_missing_steps(qa_steps: Dict[str, bool]) -> List[str]:
    """Get list of missing QA steps"""
    missing = []
    for step_key, is_complete in qa_steps.items():
        if not is_complete:
            step_description = QA_STEPS.get(step_key, step_key)
            missing.append(step_description)
    return missing

def monitor_qa_feedback(dry_run: bool = False, check_interval: int = 60):
    """Main monitoring loop with REPLY functionality"""
    
    logger.info("🚀 Starting Enhanced QA Feedback Monitor...")
    logger.info(f"{'📋 DRY RUN MODE' if dry_run else '💾 LIVE MODE'}")
    logger.info(f"⏰ Check interval: {check_interval} seconds")
    
    # Show enabled groups
    enabled_groups = get_enabled_groups()
    logger.info(f"📊 Monitoring groups: {list(enabled_groups.keys())}")
    
    if not enabled_groups:
        logger.error("❌ No groups enabled for monitoring!")
        return
    
    logger.info("=" * 70)
    
    processed_incomplete = set()
    
    while True:
        try:
            total_feedback_sent = 0
            
            for group_name, config in enabled_groups.items():
                if not config['enabled']:
                    continue
                    
                logger.debug(f"Processing {group_name}...")
                
                # Get sheet data
                sheet_data = get_sheet_data(group_name)
                if not sheet_data:
                    logger.warning(f"No data from {group_name} sheet")
                    continue
                
                for row_index, row in enumerate(sheet_data):
                    parsed_row = parse_sheet_row(row, row_index + 1)
                    if not parsed_row:
                        continue
                    
                    drop_number = parsed_row['drop_number']
                    is_incomplete = parsed_row['incomplete']
                    is_completed = parsed_row['completed']
                    
                    # Skip if completed
                    if is_completed:
                        continue
                    
                    # Check if newly incomplete
                    row_key = f"{group_name}_{drop_number}_{row_index}"
                    
                    if is_incomplete and row_key not in processed_incomplete:
                        logger.info(f"🚨 NEW INCOMPLETE: {drop_number} in {group_name}")
                        
                        # Get missing steps
                        missing_steps = get_missing_steps(parsed_row['qa_steps'])
                        
                        if missing_steps:
                            # Create feedback message
                            message = create_feedback_message(
                                drop_number, 
                                missing_steps, 
                                group_name, 
                                parsed_row['user']
                            )
                            
                            # Send REPLY to original sender
                            if send_reply_to_sender(
                                drop_number, 
                                config['group_jid'], 
                                message, 
                                dry_run
                            ):
                                total_feedback_sent += 1
                                processed_incomplete.add(row_key)
                            else:
                                logger.error(f"❌ Failed to send feedback for {drop_number}")
                        else:
                            logger.info(f"ℹ️ {drop_number}: All steps complete")
                    
                    elif not is_incomplete and row_key in processed_incomplete:
                        # No longer incomplete
                        processed_incomplete.remove(row_key)
                        logger.info(f"✅ {drop_number} no longer incomplete")
            
            if total_feedback_sent > 0:
                logger.info(f"📊 Sent {total_feedback_sent} feedback replies")
            else:
                logger.debug("✅ No new incomplete drops found")
            
            # Wait before next check
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("⚠️ Received keyboard interrupt. Shutting down...")
            break
        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
            logger.info(f"⏰ Waiting {check_interval} seconds before retry...")
            time.sleep(check_interval)
    
    logger.info("🛑 Enhanced QA Feedback Monitor stopped")

def main():
    parser = argparse.ArgumentParser(description='Enhanced QA Feedback Monitor with Reply Functionality')
    parser.add_argument('--dry-run', action='store_true', help='Preview mode - don\'t send actual messages')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    parser.add_argument('--test', action='store_true', help='Run single test check and exit')
    parser.add_argument('--enable-group', type=str, help='Enable specific group for monitoring')
    parser.add_argument('--disable-group', type=str, help='Disable specific group from monitoring')
    parser.add_argument('--show-config', action='store_true', help='Show current group configuration')
    
    args = parser.parse_args()
    
    try:
        if args.show_config:
            logger.info("📊 Current Group Configuration:")
            for name, config in GROUP_CONFIG.items():
                status = "🟢 ENABLED" if config['enabled'] else "🔴 DISABLED"
                testing = " (TESTING)" if config.get('testing_mode') else ""
                logger.info(f"  {name}: {status}{testing}")
            return
        
        if args.enable_group:
            if args.enable_group in GROUP_CONFIG:
                GROUP_CONFIG[args.enable_group]['enabled'] = True
                logger.info(f"✅ Enabled monitoring for {args.enable_group}")
            else:
                logger.error(f"❌ Unknown group: {args.enable_group}")
                return
        
        if args.disable_group:
            if args.disable_group in GROUP_CONFIG:
                GROUP_CONFIG[args.disable_group]['enabled'] = False
                logger.info(f"🔴 Disabled monitoring for {args.disable_group}")
            else:
                logger.error(f"❌ Unknown group: {args.disable_group}")
                return
        
        if args.test:
            logger.info("🧪 Running test mode...")
            # Get one sheet and process first few rows
            enabled_groups = get_enabled_groups()
            if enabled_groups:
                test_group = list(enabled_groups.keys())[0]
                sheet_data = get_sheet_data(test_group)
                logger.info(f"✅ Successfully read {len(sheet_data)} rows from {test_group}")
            return
        
        # Start monitoring
        monitor_qa_feedback(args.dry_run, args.interval)
        
    except KeyboardInterrupt:
        logger.info("⚠️ Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()