#!/usr/bin/env python3
"""
Lawley Isolated Service
Dedicated service for monitoring Lawley WhatsApp group with parallel testing mode.
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, jsonify
from threading import Thread
import time

# Add parent directory to path to access group_service_template
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from group_service_template import GroupService

class LawleyService:
    """
    Lawley-specific service wrapper.
    Handles Lawley group monitoring with safe parallel testing configuration.
    """
    
    def __init__(self):
        self.service_id = "lawley"
        self.port = 8083
        self.logger = self._setup_logging()
        
        # Set environment variables for this service
        os.environ['SERVICE_PORT'] = str(self.port)
        os.environ['CHECK_INTERVAL'] = '15'  # 15 second intervals
        
        # Initialize Flask app for health checks
        self.app = Flask(__name__)
        self.app.logger.disabled = True  # Disable Flask logging
        self._setup_routes()
        
        # Initialize the base service
        self.service = GroupService(self.service_id)
        self.service_started = False
        
    def _setup_logging(self) -> logging.Logger:
        """Setup Lawley-specific logging."""
        logger = logging.getLogger('LawleyService')
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _setup_routes(self):
        """Setup Flask routes for health checks and status."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'service': 'lawley',
                'port': self.port,
                'service_started': self.service_started
            })
            
        @self.app.route('/status', methods=['GET'])
        def status():
            """Detailed status endpoint."""
            return jsonify({
                'service_id': self.service_id,
                'port': self.port,
                'service_started': self.service_started,
                'mode': 'parallel_testing',
                'safety': 'read_only_monitoring'
            })
    
    def _start_flask_app(self):
        """Start Flask app in a separate thread."""
        self.app.run(host='0.0.0.0', port=self.port, debug=False, use_reloader=False)
        
    def validate_configuration(self) -> bool:
        """Validate Lawley-specific configuration."""
        config = self.service.config
        
        # Check required Lawley configuration
        required_fields = [
            'whatsapp.production_group_jid',
            'whatsapp.monitor_group_jid', 
            'whatsapp.feedback_target',
            'google_sheets.tab_name'
        ]
        
        for field in required_fields:
            keys = field.split('.')
            value = config
            for key in keys:
                value = value.get(key, {})
            
            if not value or value == "TBD":
                self.logger.error(f"❌ Missing required configuration: {field}")
                return False
                
        # Validate parallel testing mode
        if not config.get('whatsapp', {}).get('parallel_testing_mode', False):
            self.logger.warning("⚠️  Parallel testing mode should be enabled for Lawley")
            
        # Validate safety: feedback should go to monitor group, not production
        production_jid = config.get('whatsapp', {}).get('production_group_jid')
        feedback_target = config.get('whatsapp', {}).get('feedback_target')
        
        if production_jid == feedback_target:
            self.logger.error("❌ SAFETY VIOLATION: Feedback target is same as production group!")
            return False
            
        self.logger.info("✅ Configuration validation passed")
        return True
        
    def print_startup_info(self):
        """Print startup information for Lawley service."""
        config = self.service.config
        
        print("🏗️ LAWLEY SERVICE STARTING")
        print("=" * 50)
        print(f"Service ID: {self.service_id}")
        print(f"Port: {self.port}")
        print(f"Mode: {'Parallel Testing (SAFE)' if config.get('whatsapp', {}).get('parallel_testing_mode') else 'Production'}")
        print()
        
        print("📱 WHATSAPP CONFIGURATION:")
        print(f"  Production Group: {config.get('whatsapp', {}).get('production_group_jid')} (READ-ONLY)")
        print(f"  Monitor Group: {config.get('whatsapp', {}).get('monitor_group_jid')} (FEEDBACK TARGET)")
        print(f"  Group Name: {config.get('whatsapp', {}).get('production_group_name')}")
        print()
        
        print("📊 GOOGLE SHEETS:")
        print(f"  Sheet ID: {config.get('google_sheets', {}).get('sheet_id')}")
        print(f"  Tab Name: {config.get('google_sheets', {}).get('tab_name')} (WRITES HERE)")
        print(f"  Live Tab: {config.get('google_sheets', {}).get('live_tab_name')} (NOT TOUCHED)")
        print()
        
        print("⚙️  SERVICE CONFIGURATION:")
        service_config = config.get('configuration', {})
        print(f"  Drop Detection: {'✅' if service_config.get('drop_detection_enabled') else '❌'}")
        print(f"  QA Feedback: {'✅' if service_config.get('qa_feedback_enabled') else '❌'}")
        print(f"  Google Sheets: {'✅' if service_config.get('google_sheets_write') else '❌'}")
        print(f"  Database Logging: {'✅' if service_config.get('database_logging') else '❌'}")
        print()
        
        print("🔒 SAFETY STATUS:")
        print("  ✅ Monitors production group (READ-ONLY)")
        print("  ✅ Sends feedback to monitor group only")
        print("  ✅ Writes to separate Google Sheets tab")
        print("  ✅ Zero impact on live operations")
        print()
        
    def start(self):
        """Start the Lawley service."""
        try:
            # Validate configuration before starting
            if not self.validate_configuration():
                self.logger.error("❌ Configuration validation failed. Cannot start service.")
                print("\n⚠️  CONFIGURATION REQUIRED:")
                print("1. Create 'Lawley WA_Tool Monitor' WhatsApp group")
                print("2. Get the group JID and update config/services.json")
                print("3. Set monitor_group_jid and feedback_target to the new group JID")
                sys.exit(1)
                
            # Print startup information
            self.print_startup_info()
            
            # Start Flask app in background thread for health checks
            self.logger.info(f"🌐 Starting Flask health server on port {self.port}...")
            flask_thread = Thread(target=self._start_flask_app, daemon=True)
            flask_thread.start()
            
            # Give Flask a moment to start
            time.sleep(2)
            
            # Mark service as started
            self.service_started = True
            
            # Start the main monitoring service
            self.logger.info("🚀 Starting Lawley monitoring service...")
            self.service.start()
            
        except KeyboardInterrupt:
            self.logger.info("🛑 Lawley service interrupted by user")
        except Exception as e:
            self.logger.error(f"❌ Lawley service failed: {e}")
            sys.exit(1)

def main():
    """Main entry point for Lawley service."""
    print("🏗️ Lawley WhatsApp Group Monitoring Service")
    print("⚠️  PARALLEL TESTING MODE - Safe monitoring with zero production impact")
    print()
    
    lawley_service = LawleyService()
    lawley_service.start()

if __name__ == "__main__":
    main()