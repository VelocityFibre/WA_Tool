#!/usr/bin/env python3
"""
Robust WhatsApp Drop Number Monitor v2.0
Redesigned 2025-09-26 to fix recurring processing failures

Key Improvements:
- Comprehensive error handling and logging
- Process validation with rollback on failure
- Health checks and self-monitoring
- Redundant processing verification
- Atomic operations with transaction safety
"""

import argparse
import re
import time
import sqlite3
import psycopg2
from datetime import datetime, timedelta
from typing import Set, List, Dict, Optional, Tuple
import logging
import os
import signal
import sys
import json
import traceback

# Configuration
LAWLEY_GROUP_JID = '120363418298130331@g.us'
MESSAGES_DB_PATH = '../whatsapp-bridge/store/messages.db'
NEON_DB_URL = "postgresql://neondb_owner:npg_RIgDxzo4St6d@ep-damp-credit-a857vku0-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
DROP_PATTERN = r'DR\d{7}'
STATE_FILE = 'robust_monitor_state.json'
HEALTH_FILE = 'monitor_health.json'

# Global variables
running = True
monitor_start_time = datetime.now()

class MonitorHealth:
    def __init__(self):
        self.start_time = datetime.now()
        self.last_successful_check = None
        self.messages_processed_count = 0
        self.errors_count = 0
        self.last_error = None
        
    def record_success(self, processed_count=0):
        self.last_successful_check = datetime.now()
        self.messages_processed_count += processed_count
        self.save_health()
        
    def record_error(self, error_msg):
        self.errors_count += 1
        self.last_error = error_msg
        self.save_health()
        logger.error(f"Health check failed: {error_msg}")
        
    def save_health(self):
        try:
            health_data = {
                'start_time': self.start_time.isoformat(),
                'last_successful_check': self.last_successful_check.isoformat() if self.last_successful_check else None,
                'messages_processed_count': self.messages_processed_count,
                'errors_count': self.errors_count,
                'last_error': self.last_error,
                'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
            }
            with open(HEALTH_FILE, 'w') as f:
                json.dump(health_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save health data: {e}")

def setup_logging():
    """Set up comprehensive logging with multiple handlers."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('robust_drop_monitor.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def signal_handler(signum, frame):
    """Handle graceful shutdown with health reporting."""
    global running
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    running = False

def load_monitor_state() -> Tuple[datetime, Set[str]]:
    """Load monitor state with validation."""
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
                
            # Validate state structure
            if not isinstance(state, dict) or 'last_check_time' not in state:
                logger.warning("Invalid state file structure, resetting")
                return get_default_start_time(), set()
                
            last_check = datetime.fromisoformat(state['last_check_time'])
            processed_ids = set(state.get('processed_message_ids', []))
            
            # Sanity check - don't start from future
            if last_check > datetime.now():
                logger.warning(f"State time in future ({last_check}), resetting to 1 hour ago")
                return get_default_start_time(), set()
                
            logger.info(f"📂 Loaded state: last_check={last_check}, processed_ids={len(processed_ids)}")
            return last_check, processed_ids
            
    except Exception as e:
        logger.warning(f"Failed to load state: {e}, using defaults")
        
    return get_default_start_time(), set()

def get_default_start_time() -> datetime:
    """Get safe default start time."""
    default_time = datetime.now() - timedelta(hours=2)  # Look back 2 hours to catch any missed messages
    logger.info(f"🕐 Using default start time: {default_time}")
    return default_time

def save_monitor_state(last_check_time: datetime, processed_ids: Set[str]):
    """Save monitor state with validation."""
    try:
        # Keep only last 2000 IDs to prevent file bloat
        processed_list = list(processed_ids)
        if len(processed_list) > 2000:
            processed_list = processed_list[-2000:]
            processed_ids = set(processed_list)
        
        state = {
            'last_check_time': last_check_time.isoformat(),
            'processed_message_ids': processed_list,
            'saved_at': datetime.now().isoformat(),
            'version': '2.0'
        }
        
        # Atomic write
        temp_file = STATE_FILE + '.tmp'
        with open(temp_file, 'w') as f:
            json.dump(state, f, indent=2)
        os.rename(temp_file, STATE_FILE)
        
        logger.debug(f"💾 State saved: last_check={last_check_time}")
        
    except Exception as e:
        logger.error(f"Failed to save state: {e}")

def test_database_connections() -> bool:
    """Test both database connections with detailed error reporting."""
    logger.info("🔧 Testing database connections...")
    
    # Test SQLite
    try:
        sqlite_conn = sqlite3.connect(MESSAGES_DB_PATH, timeout=10)
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM messages LIMIT 1")
        cursor.fetchone()
        sqlite_conn.close()
        logger.info("✅ SQLite connection OK")
    except Exception as e:
        logger.error(f"❌ SQLite connection failed: {e}")
        return False
    
    # Test Neon
    try:
        neon_conn = psycopg2.connect(NEON_DB_URL, connect_timeout=10)
        cursor = neon_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        neon_conn.close()
        logger.info("✅ Neon database connection OK")
    except Exception as e:
        logger.error(f"❌ Neon database connection failed: {e}")
        return False
    
    return True

def get_latest_messages_from_sqlite(since_timestamp: datetime, processed_ids: Set[str]) -> List[Dict]:
    """Get messages with comprehensive error handling and deduplication."""
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH, timeout=30)
        cursor = conn.cursor()
        
        logger.debug(f"Querying messages since {since_timestamp}")
        
        cursor.execute("""
            SELECT id, content, sender, timestamp, is_from_me
            FROM messages 
            WHERE chat_jid = ? AND timestamp > ? AND content != '' AND content IS NOT NULL
            ORDER BY timestamp ASC
        """, (LAWLEY_GROUP_JID, since_timestamp.isoformat()))
        
        raw_messages = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in raw_messages:
            msg_id, content, sender, timestamp, is_from_me = row
            
            # Skip already processed messages
            if msg_id in processed_ids:
                logger.debug(f"Skipping already processed message {msg_id}")
                continue
                
            # Skip messages from bot itself
            if is_from_me:
                continue
                
            try:
                timestamp_obj = datetime.fromisoformat(timestamp)
            except ValueError:
                logger.warning(f"Invalid timestamp format: {timestamp}")
                continue
                
            messages.append({
                'id': msg_id,
                'content': content,
                'sender': sender,
                'timestamp': timestamp_obj,
                'is_from_me': bool(is_from_me)
            })
        
        logger.info(f"📖 Retrieved {len(messages)} new messages from SQLite")
        return messages
        
    except Exception as e:
        logger.error(f"Failed to read from SQLite: {e}")
        logger.error(traceback.format_exc())
        return []

def extract_drop_numbers_from_messages(messages: List[Dict]) -> List[Dict]:
    """Extract drop numbers with comprehensive validation."""
    found_drops = []
    
    for msg in messages:
        content = msg['content']
        drops_in_message = re.findall(DROP_PATTERN, content, re.IGNORECASE)
        
        if not drops_in_message:
            continue
            
        for drop in drops_in_message:
            drop_upper = drop.upper()
            
            # Create contractor info
            sender = msg['sender']
            contractor_name = f'WhatsApp-{sender[:20]}' if len(sender) <= 20 else f'WhatsApp-{sender[:20]}...'
            
            drop_info = {
                'drop_number': drop_upper,
                'message_id': msg['id'],
                'sender': sender,
                'contractor_name': contractor_name,
                'timestamp': msg['timestamp'],
                'message_content': content,
                'address': 'Extracted from WhatsApp Lawley Activation 3 group'
            }
            
            found_drops.append(drop_info)
            logger.info(f"🎯 Found drop number: {drop_upper} from {sender} at {msg['timestamp']}")
    
    return found_drops

def verify_drop_not_exists(neon_cursor, drop_number: str) -> bool:
    """Verify drop number doesn't already exist in Neon."""
    neon_cursor.execute("SELECT id FROM installations WHERE drop_number = %s", (drop_number,))
    return neon_cursor.fetchone() is None

def create_installation_record(neon_cursor, drop_info: Dict) -> bool:
    """Create installation record with full error handling."""
    try:
        neon_cursor.execute("""
            INSERT INTO installations (
                drop_number, contractor_name, address, status,
                completion_percentage, date_submitted, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            drop_info['drop_number'],
            drop_info['contractor_name'],
            drop_info['address'],
            'submitted',
            0,
            drop_info['timestamp'],
            drop_info['timestamp'],
            datetime.now()
        ))
        logger.info(f"✅ Created installation record for {drop_info['drop_number']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create installation for {drop_info['drop_number']}: {e}")
        return False

def create_qa_review(neon_cursor, drop_info: Dict) -> bool:
    """Create QA review with full error handling."""
    try:
        user_name = drop_info['contractor_name'].replace('WhatsApp-', '')[:20]
        
        neon_cursor.execute("""
            INSERT INTO qa_photo_reviews (
                drop_number, review_date, user_name,
                step_01_property_frontage, step_02_location_before_install, 
                step_03_outside_cable_span, step_04_home_entry_outside, 
                step_05_home_entry_inside, step_06_fibre_entry_to_ont,
                step_07_patched_labelled_drop, step_08_work_area_completion,
                step_09_ont_barcode_scan, step_10_ups_serial_number,
                step_11_powermeter_reading, step_12_powermeter_at_ont,
                step_13_active_broadband_light, step_14_customer_signature,
                outstanding_photos_loaded_to_1map
            ) VALUES (%s, CURRENT_DATE, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            drop_info['drop_number'], user_name,
            False, False, False, False, False, False, False, False,
            False, False, False, False, False, False, False
        ))
        logger.info(f"✅ Created QA review for {drop_info['drop_number']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create QA review for {drop_info['drop_number']}: {e}")
        return False

def process_drop_numbers_to_neon(drop_numbers: List[Dict], dry_run: bool = False) -> int:
    """Process drop numbers with atomic transactions and validation."""
    if not drop_numbers:
        return 0
        
    if dry_run:
        logger.info(f"🔍 DRY RUN: Would process {len(drop_numbers)} drop numbers")
        for drop_info in drop_numbers:
            logger.info(f"🔍 Would create records for {drop_info['drop_number']}")
        return len(drop_numbers)
    
    processed_count = 0
    
    try:
        neon_conn = psycopg2.connect(NEON_DB_URL, connect_timeout=30)
        neon_conn.set_session(autocommit=False)  # Explicit transaction control
        neon_cursor = neon_conn.cursor()
        
        for drop_info in drop_numbers:
            drop_number = drop_info['drop_number']
            
            try:
                # Start transaction for this drop
                logger.info(f"🔄 Processing {drop_number}...")
                
                # Check if already exists
                if not verify_drop_not_exists(neon_cursor, drop_number):
                    logger.info(f"⚠️ {drop_number}: Already exists in database, skipping")
                    continue
                
                # Create installation record
                if not create_installation_record(neon_cursor, drop_info):
                    logger.error(f"Failed to create installation for {drop_number}")
                    continue
                
                # Create QA review
                if not create_qa_review(neon_cursor, drop_info):
                    logger.error(f"Failed to create QA review for {drop_number}")
                    # Rollback the installation too
                    neon_conn.rollback()
                    continue
                
                # Commit this drop's transaction
                neon_conn.commit()
                processed_count += 1
                logger.info(f"🎉 Successfully processed {drop_number}")
                
            except Exception as e:
                logger.error(f"Error processing {drop_number}: {e}")
                neon_conn.rollback()
                continue
        
        neon_conn.close()
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return 0
    
    logger.info(f"✅ Successfully processed {processed_count}/{len(drop_numbers)} drop numbers")
    return processed_count

def run_monitor_cycle(last_check_time: datetime, processed_ids: Set[str], health: MonitorHealth, dry_run: bool = False) -> Tuple[datetime, Set[str]]:
    """Run one monitor cycle with comprehensive error handling."""
    try:
        # Get new messages
        messages = get_latest_messages_from_sqlite(last_check_time, processed_ids)
        
        if not messages:
            logger.debug("No new messages found")
            health.record_success(0)
            # Only advance time if we successfully checked
            return datetime.now(), processed_ids
        
        # Extract drop numbers
        drop_numbers = extract_drop_numbers_from_messages(messages)
        
        if not drop_numbers:
            logger.info(f"📋 Processed {len(messages)} messages, no drop numbers found")
            # Mark all messages as processed
            new_processed_ids = processed_ids.copy()
            for msg in messages:
                new_processed_ids.add(msg['id'])
            health.record_success(0)
            return messages[-1]['timestamp'], new_processed_ids
        
        # Process to Neon database
        processed_count = process_drop_numbers_to_neon(drop_numbers, dry_run)
        
        if processed_count == 0:
            health.record_error(f"Failed to process any of {len(drop_numbers)} drop numbers")
            return last_check_time, processed_ids  # Don't advance on failure
        
        # Mark messages as processed only on success
        new_processed_ids = processed_ids.copy()
        latest_timestamp = last_check_time
        
        for msg in messages:
            new_processed_ids.add(msg['id'])
            if msg['timestamp'] > latest_timestamp:
                latest_timestamp = msg['timestamp']
        
        health.record_success(processed_count)
        logger.info(f"🎉 Cycle complete: processed {processed_count} drop numbers from {len(messages)} messages")
        
        return latest_timestamp, new_processed_ids
        
    except Exception as e:
        logger.error(f"Monitor cycle failed: {e}")
        logger.error(traceback.format_exc())
        health.record_error(str(e))
        return last_check_time, processed_ids  # Don't advance state on error

def main():
    global running, logger
    
    parser = argparse.ArgumentParser(description='Robust WhatsApp Drop Number Monitor v2.0')
    parser.add_argument('--interval', type=int, default=15, help='Check interval in seconds (minimum 5)')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode (no database writes)')
    args = parser.parse_args()
    
    # Setup
    logger = setup_logging()
    health = MonitorHealth()
    
    # Validate interval
    if args.interval < 5:
        logger.warning(f"⚠️ Minimum interval is 5 seconds. Setting to 5.")
        args.interval = 5
    
    # Signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Starting Robust Drop Number Monitor v2.0...")
    if args.dry_run:
        logger.info("📋 DRY RUN MODE - No database writes will be performed")
    else:
        logger.info("💾 LIVE MODE - Will write to databases")
    
    logger.info(f"⏰ Check interval: {args.interval} seconds")
    logger.info(f"👀 Monitoring group: {LAWLEY_GROUP_JID}")
    logger.info("=" * 70)
    
    # Test database connections
    if not test_database_connections():
        logger.error("❌ Database connection tests failed, exiting")
        sys.exit(1)
    
    # Load state
    last_check_time, processed_ids = load_monitor_state()
    
    # Main loop
    logger.info("🎯 Monitor loop started")
    
    while running:
        try:
            cycle_start = datetime.now()
            
            # Run monitoring cycle
            new_last_check, new_processed_ids = run_monitor_cycle(
                last_check_time, processed_ids, health, args.dry_run
            )
            
            # Save state only if cycle succeeded
            if new_last_check != last_check_time or new_processed_ids != processed_ids:
                save_monitor_state(new_last_check, new_processed_ids)
                last_check_time = new_last_check
                processed_ids = new_processed_ids
            
            # Sleep for remainder of interval
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            sleep_time = max(0, args.interval - cycle_duration)
            
            if sleep_time > 0:
                time.sleep(sleep_time)
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            logger.error(traceback.format_exc())
            health.record_error(f"Main loop error: {e}")
            time.sleep(args.interval)  # Wait before retry
    
    # Cleanup
    runtime = datetime.now() - monitor_start_time
    logger.info(f"🛑 Monitor stopped after {runtime}")
    logger.info(f"📊 Messages processed: {health.messages_processed_count}")
    logger.info(f"❌ Errors encountered: {health.errors_count}")
    logger.info("👋 Goodbye!")

if __name__ == "__main__":
    main()