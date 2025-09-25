#!/usr/bin/env python3
"""
Script to send a message via WhatsApp
"""
import requests
import json
import sys

# WhatsApp Bridge API endpoint
API_URL = "http://localhost:8080/api/send"

# Recipient phone number (US number)
RECIPIENT = "12145432065@s.whatsapp.net"

# Message content
MESSAGE = "the the deep insights and knowledge is very valuable for them ! lots to watch and concider the holiday (:"

def send_message():
    """Send message to recipient via WhatsApp Bridge API"""
    payload = {
        "recipient": RECIPIENT,
        "message": MESSAGE
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get("success"):
            print(f"Message sent successfully to {RECIPIENT}")
            return True
        else:
            print(f"Failed to send message: {response_data.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"Sending message to {RECIPIENT}...")
    send_message()
