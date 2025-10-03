#!/usr/bin/env python3
"""
Google Sheets QA Monitor - Watches for "Incomplete" checkbox changes
=====================================================================

Monitors the Google Sheets "Velo Test" tab for when the "Incomplete" 
checkbox (column V) is ticked and triggers QA feedback communication 
to the WhatsApp group.
"""

import os
import time
import logging
import sys
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

# Import existing QA feedback system
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import psycopg2

# Set up logger first for imported modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('google_sheets_qa_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

from qa_feedback_communicator import (
    get_missing_steps, create_feedback_message, send_feedback_to_group, 
    mark_feedback_sent, QA_STEPS, PROJECTS, NEON_DB_URL
)

# Configuration
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GSHEET_ID = os.getenv("GSHEET_ID")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
# Support multiple sheet tabs
SHEET_NAMES = ["Velo Test", "Mohadin"]

# State tracking
MONITOR_STATE_FILE = 'google_sheets_qa_monitor_state.json'

def setup_logging():
    """Set up logging configuration (already done at module level)"""
    return logger

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

def check_environment():
    """Check if all required environment variables are set"""
    if not GSHEET_ID:
        raise EnvironmentError("GSHEET_ID environment variable not set")
    
    if not GOOGLE_APPLICATION_CREDENTIALS:
        raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")
    
    if not os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
        raise FileNotFoundError(f"Credentials file not found: {GOOGLE_APPLICATION_CREDENTIALS}")

def get_sheet_data(sheet_name=None):
    """Get all data from the specified sheet (or all sheets if None)"""
    try:
        service = get_sheets_service()
        if not service:
            return None
            
        if sheet_name:
            # Get data from specific sheet
            result = service.spreadsheets().values().get(
                spreadsheetId=GSHEET_ID,
                range=f"{sheet_name}!A:X"
            ).execute()
            
            values = result.get('values', [])
            return {sheet_name: values}
        else:
            # Get data from all monitored sheets
            all_data = {}
            for sheet in SHEET_NAMES:
                try:
                    result = service.spreadsheets().values().get(
                        spreadsheetId=GSHEET_ID,
                        range=f"{sheet}!A:X"
                    ).execute()
                    all_data[sheet] = result.get('values', [])
                except Exception as e:
                    logger.warning(f"Could not read {sheet} sheet: {e}")
                    all_data[sheet] = []
            return all_data
        
    except Exception as e:
        logger.error(f"Error reading sheet data: {e}")
        return None

def parse_sheet_row(row: List, row_number: int) -> Optional[Dict]:
    """Parse a sheet row into a structured dictionary"""
    try:
        # Ensure row has enough columns - now up to column X
        while len(row) < 24:  # Up to column X
            row.append('')
        
        # Skip header rows and empty drop numbers
        if row_number <= 2 or not row[1].strip():  # Column B is drop number
            return None
            
        drop_number = row[1].strip()
        if not drop_number.startswith('DR'):
            return None
            
        # Parse the row data
        parsed = {
            'row_number': row_number,
            'drop_number': drop_number,
            'date': row[0] if len(row) > 0 else '',
            'qa_steps': {
                'step_01_property_frontage': row[2].lower() == 'true' if len(row) > 2 else False,
                'step_02_location_before_install': row[3].lower() == 'true' if len(row) > 3 else False,
                'step_03_outside_cable_span': row[4].lower() == 'true' if len(row) > 4 else False,
                'step_04_home_entry_outside': row[5].lower() == 'true' if len(row) > 5 else False,
                'step_05_home_entry_inside': row[6].lower() == 'true' if len(row) > 6 else False,
                'step_06_fibre_entry_to_ont': row[7].lower() == 'true' if len(row) > 7 else False,
                'step_07_patched_labelled_drop': row[8].lower() == 'true' if len(row) > 8 else False,
                'step_08_work_area_completion': row[9].lower() == 'true' if len(row) > 9 else False,
                'step_09_ont_barcode_scan': row[10].lower() == 'true' if len(row) > 10 else False,
                'step_10_ups_serial_number': row[11].lower() == 'true' if len(row) > 11 else False,
                'step_11_powermeter_reading': row[12].lower() == 'true' if len(row) > 12 else False,
                'step_12_powermeter_at_ont': row[13].lower() == 'true' if len(row) > 13 else False,
                'step_13_active_broadband_light': row[14].lower() == 'true' if len(row) > 14 else False,
                'step_14_customer_signature': row[15].lower() == 'true' if len(row) > 15 else False,
            },
            'completed_photos': int(row[16]) if len(row) > 16 and row[16].isdigit() else 0,
            'outstanding_photos': int(row[17]) if len(row) > 17 and row[17].isdigit() else 14,
            'user': row[18] if len(row) > 18 else '',
            'one_map_loaded': row[19] if len(row) > 19 else '',
            'comment': row[20] if len(row) > 20 else '',
            'incomplete': row[21].lower() == 'true' if len(row) > 21 else False,  # Column V
            'resubmitted': row[22].lower() == 'true' if len(row) > 22 else False,  # Column W
            'completed': row[23].lower() == 'true' if len(row) > 23 else False,  # Column X
        }
        
        return parsed
        
    except Exception as e:
        logger.error(f"Error parsing row {row_number}: {e}")
        return None

def sync_incomplete_to_neon(drop_number: str, incomplete: bool) -> bool:
    """Update the Neon database when incomplete status changes (optional)"""
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor()
        
        # Try to update qa_photo_reviews table if record exists
        cursor.execute("""
            UPDATE qa_photo_reviews 
            SET incomplete = %s, 
                updated_at = CURRENT_TIMESTAMP,
                feedback_sent = NULL
            WHERE drop_number = %s
        """, (incomplete, drop_number))
        
        if cursor.rowcount > 0:
            conn.commit()
            logger.info(f"📝 Updated {drop_number} incomplete status to {incomplete} in Neon")
        else:
            logger.info(f"ℹ️  Drop {drop_number} not in Neon database - will use sheet data only")
            
        cursor.close()
        conn.close()
        return True  # Always return True - sheet data is primary source
        
    except Exception as e:
        logger.warning(f"⚠️  Could not update Neon database for {drop_number}: {e}")
        return True  # Continue with sheet-only processing

def trigger_qa_feedback(drop_data: Dict, dry_run: bool = False) -> bool:
    """Trigger QA feedback communication for incomplete drop"""
    # Get logger - use module logger if available, otherwise create basic logging
    try:
        current_logger = logger
    except NameError:
        import logging
        current_logger = logging.getLogger(__name__)
        current_logger.setLevel(logging.INFO)
        if not current_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            current_logger.addHandler(handler)
        
    try:
        drop_number = drop_data['drop_number']
        user = drop_data['user'] or 'Not specified'
        
        # Get missing steps
        missing_steps = get_missing_steps(drop_data['qa_steps'])
        
        if not missing_steps:
            current_logger.info(f"ℹ️  {drop_number}: All steps complete, nothing to communicate")
            return False
        
        current_logger.info(f"🔍 {drop_number}: {len(missing_steps)} missing steps - sending feedback")
        
        # Determine project from sheet name
        project_name = drop_data.get('sheet_name', 'Velo Test')
        
        # Create feedback message
        message = create_feedback_message(drop_number, missing_steps, project_name, user)
        
        # Send to appropriate project group
        success = send_feedback_to_group(project_name, message, dry_run)
        
        if success and not dry_run:
            # Try to mark as sent in Neon database if record exists
            try:
                mark_feedback_sent(drop_number)
            except Exception as e:
                current_logger.info(f"ℹ️  Could not mark feedback sent in Neon for {drop_number}: {e}")
                # Continue - this is not critical for sheet-based workflow
            
        return success
        
    except Exception as e:
        current_logger.error(f"❌ Error triggering QA feedback for {drop_data['drop_number']}: {e}")
        return False

def monitor_sheets_for_incomplete(dry_run: bool = False, check_interval: int = 60):
    """Main monitoring loop for multiple sheets"""
    
    logger.info("🚀 Starting Google Sheets QA Monitor...")
    logger.info(f"{'📋 DRY RUN MODE' if dry_run else '💾 LIVE MODE'}")
    logger.info(f"⏰ Check interval: {check_interval} seconds")
    logger.info(f"📊 Monitoring sheets: {', '.join(SHEET_NAMES)}")
    logger.info(f"🎯 Watching column V (Incomplete) for changes")
    logger.info("=" * 70)
    
    # Track previously processed incomplete flags
    processed_incomplete = set()
    
    while True:
        try:
            # Get current data from all sheets
            all_sheet_data = get_sheet_data()
            if not all_sheet_data:
                logger.error("❌ Could not read sheet data")
                time.sleep(check_interval)
                continue
            
            # Process each sheet
            total_incomplete_found = 0
            total_feedback_sent = 0
            
            for sheet_name, sheet_data in all_sheet_data.items():
                if not sheet_data:
                    continue
                    
                logger.debug(f"Processing {sheet_name} sheet...")
                incomplete_found = 0
                feedback_sent = 0
                
                for row_index, row in enumerate(sheet_data):
                    parsed_row = parse_sheet_row(row, row_index + 1)
                    if not parsed_row:
                        continue
                    
                    # Add sheet context to parsed row
                    parsed_row['sheet_name'] = sheet_name
                    
                    drop_number = parsed_row['drop_number']
                    is_incomplete = parsed_row['incomplete']
                    is_completed = parsed_row['completed']
                    
                    # Skip if completed - no more processing needed
                    if is_completed:
                        continue
                        
                    # Check if this drop is newly marked as incomplete
                    row_key = f"{sheet_name}_{drop_number}_{row_index}"
                    
                    if is_incomplete:
                        incomplete_found += 1
                        
                        if row_key not in processed_incomplete:
                            logger.info(f"🚨 NEW INCOMPLETE: {drop_number} (Row {row_index + 1})")
                            
                            # Sync to Neon database (optional, won't block sheet processing)
                            sync_incomplete_to_neon(drop_number, True)
                            
                            # Trigger QA feedback based on sheet data
                            if trigger_qa_feedback(parsed_row, dry_run):
                                feedback_sent += 1
                                processed_incomplete.add(row_key)
                            else:
                                logger.error(f"❌ Failed to send feedback for {drop_number}")
                    else:
                        # Remove from processed set if no longer incomplete
                        if row_key in processed_incomplete:
                            processed_incomplete.remove(row_key)
                            logger.info(f"✅ {drop_number} no longer incomplete")
            
            # Log summary
            if incomplete_found > 0:
                logger.info(f"📊 Found {incomplete_found} incomplete drops, sent {feedback_sent} feedback messages")
            else:
                logger.debug(f"✅ No incomplete drops found")
                
            # Wait before next check
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("⚠️  Received keyboard interrupt. Shutting down...")
            break
        except Exception as e:
            logger.error(f"❌ Error in monitoring loop: {e}")
            logger.info(f"⏰ Waiting {check_interval} seconds before retry...")
            time.sleep(check_interval)
    
    logger.info("🛑 Google Sheets QA Monitor stopped")

def main():
    # Logger is already initialized at module level
    setup_logging()  # For compatibility, but logger is already set
    
    parser = argparse.ArgumentParser(description='Google Sheets QA Monitor for Incomplete Flags')
    parser.add_argument('--dry-run', action='store_true', help='Preview mode - don\'t actually send messages')
    parser.add_argument('--interval', type=int, default=60, help='Check interval in seconds (default: 60)')
    parser.add_argument('--test', action='store_true', help='Run single test check and exit')
    
    args = parser.parse_args()
    
    try:
        # Check environment
        check_environment()
        logger.info("✅ Environment check passed")
        
        if args.test:
            logger.info("🧪 Running single test check...")
            sheet_data = get_sheet_data()
            if sheet_data:
                logger.info(f"✅ Successfully read {len(sheet_data)} rows from sheet")
                # Process first few rows as test
                for i in range(min(5, len(sheet_data))):
                    parsed = parse_sheet_row(sheet_data[i], i + 1)
                    if parsed:
                        logger.info(f"Row {i+1}: {parsed['drop_number']} - Incomplete: {parsed['incomplete']}")
            else:
                logger.error("❌ Test failed - could not read sheet data")
            return
            
        # Start monitoring
        monitor_sheets_for_incomplete(args.dry_run, args.interval)
        
    except KeyboardInterrupt:
        logger.info("⚠️  Process interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()