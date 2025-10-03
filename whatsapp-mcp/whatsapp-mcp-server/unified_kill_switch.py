#!/usr/bin/env python3
"""
Unified Kill Switch Service
==========================

Monitors all WhatsApp groups for KILL commands and shuts down all Docker services immediately.
This runs as a separate service alongside all other monitors.

Features:
- Monitors for "KILL" commands in any enabled WhatsApp group
- Immediately shuts down all Docker Compose services
- Works in containerized and local environments
- Provides emergency stop for entire monitoring system

Date: October 2nd, 2025
"""

import os
import time
import logging
import sys
import sqlite3
import subprocess
from datetime import datetime
from typing import Dict, List, Optional
import signal

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - KILL-SWITCH - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kill_switch.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configuration
WHATSAPP_DB_PATH = "../whatsapp-bridge/store/messages.db"
DOCKER_COMPOSE_PATH = "/home/louisdup/VF/Apps/WA_Tool"

# GROUP CONFIGURATION - Monitor all enabled groups for kill commands
GROUP_CONFIG = {
    'Velo Test': {
        'group_jid': '120363421664266245@g.us',
        'group_name': 'Velo Test',
        'enabled': True,  # 🔥 ENABLED for testing
    },
    'Mohadin': {
        'group_jid': '120363421532174586@g.us',
        'group_name': 'Mohadin Activations 🥳',
        'enabled': False,  # 🚫 DISABLED during testing
    },
    'Lawley': {
        'group_jid': '120363418298130331@g.us',
        'group_name': 'Lawley Activation 3',
        'enabled': False,  # 🚫 DISABLED during testing
    }
}

def get_enabled_groups() -> Dict[str, Dict]:
    """Get only enabled groups for monitoring"""
    enabled = {name: config for name, config in GROUP_CONFIG.items() if config['enabled']}
    logger.info(f"🔍 KILL-SWITCH monitoring groups: {list(enabled.keys())}")
    return enabled

def check_for_kill_commands(since_timestamp: Optional[float] = None) -> bool:
    """Check for KILL commands in WhatsApp messages"""
    try:
        # Connect to WhatsApp Bridge SQLite database
        whatsapp_db = os.path.abspath(WHATSAPP_DB_PATH)
        if not os.path.exists(whatsapp_db):
            logger.warning(f"⚠️ WhatsApp database not found: {whatsapp_db}")
            return False
        
        conn = sqlite3.connect(whatsapp_db)
        cursor = conn.cursor()
        
        enabled_groups = get_enabled_groups()
        group_jids = [config['group_jid'] for config in enabled_groups.values()]
        
        if not group_jids:
            logger.info("No enabled groups to monitor")
            return False
        
        # Build query for all enabled groups
        placeholders = ','.join('?' * len(group_jids))
        
        if since_timestamp:
            # Check messages since last check
            cursor.execute(f"""
                SELECT id, content, sender, chat_jid, timestamp 
                FROM messages 
                WHERE chat_jid IN ({placeholders})
                AND timestamp > ?
                AND (UPPER(content) LIKE '%KILL%' OR UPPER(content) = 'KILL')
                ORDER BY timestamp DESC
            """, group_jids + [since_timestamp])
        else:
            # Check recent messages (last 5 minutes)
            recent_timestamp = time.time() - 300  # 5 minutes ago
            cursor.execute(f"""
                SELECT id, content, sender, chat_jid, timestamp 
                FROM messages 
                WHERE chat_jid IN ({placeholders})
                AND timestamp > ?
                AND (UPPER(content) LIKE '%KILL%' OR UPPER(content) = 'KILL')
                ORDER BY timestamp DESC
            """, group_jids + [recent_timestamp])
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if results:
            for message_id, content, sender, chat_jid, timestamp in results:
                # Find group name
                group_name = "Unknown"
                for name, config in enabled_groups.items():
                    if config['group_jid'] == chat_jid:
                        group_name = name
                        break
                
                dt = datetime.fromtimestamp(timestamp)
                logger.critical(f"🚨 KILL COMMAND DETECTED!")
                logger.critical(f"   Group: {group_name}")
                logger.critical(f"   Sender: {sender}")
                logger.critical(f"   Message: {content}")
                logger.critical(f"   Time: {dt}")
                logger.critical(f"   Message ID: {message_id}")
                return True
        
        return False
            
    except Exception as e:
        logger.error(f"❌ Error checking for kill commands: {e}")
        return False

def shutdown_all_services():
    """Shutdown all Docker Compose services immediately"""
    try:
        logger.critical("🚨 EMERGENCY SHUTDOWN INITIATED")
        logger.critical("Stopping all Docker Compose services...")
        
        # Change to Docker Compose directory
        os.chdir(DOCKER_COMPOSE_PATH)
        
        # Stop all services
        result = subprocess.run([
            'docker-compose', 'down', '--remove-orphans'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.critical("✅ All Docker services stopped successfully")
        else:
            logger.error(f"⚠️ Docker compose down failed: {result.stderr}")
            
        # Force kill any remaining containers
        logger.critical("🔧 Force stopping any remaining containers...")
        subprocess.run(['docker', 'stop', '$(docker', 'ps', '-q)'], 
                      shell=True, capture_output=True, timeout=10)
        
        logger.critical("🛑 EMERGENCY SHUTDOWN COMPLETE")
        
        # Exit this process
        sys.exit(0)
        
    except Exception as e:
        logger.critical(f"❌ CRITICAL ERROR during shutdown: {e}")
        # Force exit anyway
        os._exit(1)

def run_kill_switch_monitor(check_interval: int = 5):
    """Main kill switch monitoring loop"""
    logger.info(f"🚨 KILL SWITCH SERVICE STARTED")
    logger.info(f"   Check interval: {check_interval} seconds")
    logger.info(f"   Monitoring enabled groups: {list(get_enabled_groups().keys())}")
    logger.info(f"   Database: {WHATSAPP_DB_PATH}")
    
    last_check_timestamp = time.time()
    
    try:
        while True:
            # Check for kill commands
            if check_for_kill_commands(last_check_timestamp):
                logger.critical("🚨 KILL COMMAND RECEIVED - SHUTTING DOWN ALL SERVICES!")
                shutdown_all_services()
                break  # This shouldn't be reached due to sys.exit()
            
            last_check_timestamp = time.time()
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        logger.info("Kill switch monitor stopped by user")
    except Exception as e:
        logger.error(f"Kill switch monitor error: {e}")

def signal_handler(signum, frame):
    """Handle system signals"""
    logger.info(f"Received signal {signum}, shutting down kill switch monitor")
    sys.exit(0)

if __name__ == "__main__":
    import argparse
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    parser = argparse.ArgumentParser(description='Unified Kill Switch Monitor')
    parser.add_argument('--interval', type=int, default=5, 
                       help='Check interval in seconds (default: 5)')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("🚨 UNIFIED KILL SWITCH SERVICE")
    logger.info("=" * 60)
    
    run_kill_switch_monitor(args.interval)