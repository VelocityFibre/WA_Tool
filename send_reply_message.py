#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp-mcp/whatsapp-mcp-server'))
import whatsapp

# Format recipient number with country code
recipient_number = '27722426204'

# Message to send
message = """wow brother, what a blessing. I pray and say Amen to all that for You, me and all our brothers.

I saw this yesterday and wanted to share with you.
I ties into what u just shared !

Maybe remind a group of us dialy ?! the declaration !

https://youtu.be/F4K_PHDaxDM?si=Hqaki8dfWDmihOVv"""

# Send message
result, message_response = whatsapp.send_message(recipient_number, message)
print(f'Sending message to {recipient_number}: "{message[:30]}..."')
print(f'Success: {result}, Message: {message_response}')
