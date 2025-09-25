#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp-mcp/whatsapp-mcp-server'))
import whatsapp

# Format recipient number with country code
recipient_number = '2749151237303'

# Message to send (split into multiple messages due to length)
message = """Calling those things that be not as if they are - this is the life Changing Truth that made ordinary men great.  These are daily declarations that turns your day into purpose, fills it with an atmosphere of power and arms you with a Victorious Spirit. I Have a declaration for a free declaration PDF for you to download. To subscribe - mail todaywithshaun@gmail.com

Day 1: Five-Minute Morning Declarations
(Speak boldly aloud, preferably standing as a posture of spiritual authority)

I Decree and Declare: Who I Am in Christ
"I am a new creation in Christ. The old has passed away, behold, the new has come." — 2 Corinthians 5:17
* I decree and declare: I am the righteousness of God in Christ Jesus. (2 Corinthians 5:21)
* I am God's workmanship, created in Christ Jesus for good works. (Ephesians 2:10)
* I am chosen, royal, holy, and set apart for His purpose. (1 Peter 2:9)
* I am a child of God, born not of flesh but of His will. (John 1:12-13)
* I have been crucified with Christ, and now Christ lives in me. (Galatians 2:20)"""

# Send message
result, message_response = whatsapp.send_message(recipient_number, message)
print(f'Sending message to {recipient_number}: "{message[:30]}..."')
print(f'Success: {result}, Message: {message_response}')
