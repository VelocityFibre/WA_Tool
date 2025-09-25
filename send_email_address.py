#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp-mcp/whatsapp-mcp-server'))
import whatsapp

# Format recipient number with country code
recipient_number = '27823216574'

# Message to send
message = """Here's the email address you requested:
ai@velocityfibre.co.za"""

# Send message
result, message_response = whatsapp.send_message(recipient_number, message)
print(f'Sending message to {recipient_number}: "{message[:30]}..."')
print(f'Success: {result}, Message: {message_response}')
