#!/usr/bin/env python3
"""
Message scheduler for WhatsApp Assistant
"""
import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to scheduled messages file
SCHEDULED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/scheduled.json')

# WhatsApp MCP URL
WHATSAPP_MCP_URL = os.environ.get('WHATSAPP_MCP_URL', 'http://localhost:3000')

class MessageScheduler:
    """Handles scheduling and sending of WhatsApp messages"""
    
    def __init__(self):
        """Initialize the scheduler"""
        self.scheduled_messages = []
        self.running = False
        self.thread = None
        self.load_scheduled_messages()
    
    def load_scheduled_messages(self):
        """Load scheduled messages from file"""
        os.makedirs(os.path.dirname(SCHEDULED_FILE), exist_ok=True)
        
        if os.path.exists(SCHEDULED_FILE):
            try:
                with open(SCHEDULED_FILE, 'r') as f:
                    self.scheduled_messages = json.load(f)
                logger.info(f"Loaded {len(self.scheduled_messages)} scheduled messages")
            except Exception as e:
                logger.error(f"Error loading scheduled messages: {e}")
                self.scheduled_messages = []
        else:
            self.scheduled_messages = []
            self.save_scheduled_messages()
    
    def save_scheduled_messages(self):
        """Save scheduled messages to file"""
        try:
            with open(SCHEDULED_FILE, 'w') as f:
                json.dump(self.scheduled_messages, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving scheduled messages: {e}")
            return False
    
    def schedule_message(self, recipient, message, send_time, metadata=None):
        """Schedule a new message"""
        # Validate send_time format (ISO format)
        try:
            send_datetime = datetime.fromisoformat(send_time)
        except ValueError:
            logger.error(f"Invalid send_time format: {send_time}")
            return False
        
        # Create message object
        message_obj = {
            "id": str(int(time.time() * 1000)),  # Timestamp as ID
            "recipient": recipient,
            "message": message,
            "send_time": send_time,
            "created_at": datetime.now().isoformat(),
            "status": "scheduled",
            "metadata": metadata or {}
        }
        
        # Add to scheduled messages
        self.scheduled_messages.append(message_obj)
        self.save_scheduled_messages()
        
        # Start scheduler if not running
        self.ensure_scheduler_running()
        
        return message_obj["id"]
    
    def cancel_message(self, message_id):
        """Cancel a scheduled message"""
        for i, msg in enumerate(self.scheduled_messages):
            if msg["id"] == message_id:
                if msg["status"] == "scheduled":
                    # Remove from list
                    del self.scheduled_messages[i]
                    self.save_scheduled_messages()
                    return True
                else:
                    # Can't cancel already sent messages
                    return False
        
        # Message not found
        return False
    
    def get_scheduled_messages(self, recipient=None):
        """Get all scheduled messages, optionally filtered by recipient"""
        if recipient:
            return [msg for msg in self.scheduled_messages if msg["recipient"] == recipient and msg["status"] == "scheduled"]
        else:
            return [msg for msg in self.scheduled_messages if msg["status"] == "scheduled"]
    
    def get_message_history(self, limit=100):
        """Get history of sent scheduled messages"""
        sent_messages = [msg for msg in self.scheduled_messages if msg["status"] == "sent"]
        sent_messages.sort(key=lambda x: x.get("sent_at", ""), reverse=True)
        return sent_messages[:limit]
    
    def ensure_scheduler_running(self):
        """Ensure the scheduler thread is running"""
        if not self.running or (self.thread and not self.thread.is_alive()):
            self.running = True
            self.thread = threading.Thread(target=self._scheduler_loop)
            self.thread.daemon = True
            self.thread.start()
            logger.info("Message scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler thread"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
            logger.info("Message scheduler stopped")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            now = datetime.now()
            
            # Find messages that need to be sent
            for msg in self.scheduled_messages:
                if msg["status"] == "scheduled":
                    try:
                        send_time = datetime.fromisoformat(msg["send_time"])
                        if send_time <= now:
                            # Time to send this message
                            self._send_message(msg)
                    except Exception as e:
                        logger.error(f"Error processing scheduled message: {e}")
                        msg["status"] = "error"
                        msg["error"] = str(e)
            
            # Save any status changes
            self.save_scheduled_messages()
            
            # Sleep for a bit
            time.sleep(10)  # Check every 10 seconds
    
    def _send_message(self, message):
        """Send a scheduled message via WhatsApp MCP"""
        try:
            # Call WhatsApp MCP API
            response = requests.post(f"{WHATSAPP_MCP_URL}/send", json={
                "recipient": message["recipient"],
                "message": message["message"]
            })
            
            if response.status_code == 200 and response.json().get("success"):
                # Message sent successfully
                message["status"] = "sent"
                message["sent_at"] = datetime.now().isoformat()
                logger.info(f"Scheduled message sent to {message['recipient']}")
                return True
            else:
                # Failed to send
                message["status"] = "error"
                message["error"] = response.text
                logger.error(f"Error sending scheduled message: {response.text}")
                return False
        except Exception as e:
            # Exception occurred
            message["status"] = "error"
            message["error"] = str(e)
            logger.error(f"Exception sending scheduled message: {e}")
            return False

# Create a singleton instance
scheduler = MessageScheduler()
