#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp-mcp/whatsapp-mcp-server'))
import whatsapp

# Send message to 27640412391 with the provided URL
recipient = '27640412391'
message = 'https://app.coupler.io/export/w/0fe17d53-a5a0-462e-ba86-d25590f8457a.json?access_token=8f5511d494cb4368f2b2e6ef7a9512bd5a14d1673eb2722edaf39da89546'
result, message_response = whatsapp.send_message(recipient, message)
print(f'Sending message to {recipient}: "{message}"')
print(f'Success: {result}, Message: {message_response}')
