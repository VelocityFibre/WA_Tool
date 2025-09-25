#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp-mcp/whatsapp-mcp-server'))
import whatsapp

# Format recipient number with country code
recipient_number = '27823216574'

# Message to send
message = """I have a powerful declaration for you that can transform your day into purpose, fill it with an atmosphere of power, and arm you with a victorious spirit. Would you like to receive it?"""

# Send message
result, message_response = whatsapp.send_message(recipient_number, message)
print(f'Sending message to {recipient_number}: "{message[:30]}..."')
print(f'Success: {result}, Message: {message_response}')
