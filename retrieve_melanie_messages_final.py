#!/usr/bin/env python3
import sys
import os
import json
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp-mcp/whatsapp-mcp-server'))
import whatsapp

# Load contacts from contacts.json
def load_contacts():
    with open('contacts.json', 'r') as f:
        return json.load(f)

# Find contact by name
def find_contact(contacts, name):
    for contact in contacts:
        if contact['name'].lower() == name.lower():
            return contact
    return None

# Format phone number with proper country code
def format_phone_number(number):
    if not number.startswith('27'):
        # Remove leading 0 if present and add country code
        if number.startswith('0'):
            number = '27' + number[1:]
        else:
            number = '27' + number
    return number

# Main function
if __name__ == "__main__":
    contacts = load_contacts()
    melanie = find_contact(contacts, "Melanie")
    
    if melanie:
        # Format the number with WhatsApp JID format
        number = format_phone_number(melanie['number'])
        jid = f"{number}@s.whatsapp.net"
        print(f"Retrieving messages from Melanie ({jid})...")
        
        try:
            # Get chat info first
            chat = whatsapp.get_direct_chat_by_contact(number)
            if not chat:
                print(f"No chat found with Melanie ({jid})")
                sys.exit(1)
                
            print(f"Found chat with Melanie")
            
            # Get messages from this chat
            messages = whatsapp.list_messages(
                sender_phone_number=number,
                limit=100,
                include_context=False
            )
            
            if not messages:
                print(f"No messages found from Melanie ({jid})")
                sys.exit(0)
                
            # Display messages
            print(f"\nMessages from Melanie ({jid}):\n")
            print("-" * 80)
            
            for msg in messages:
                # Format timestamp
                formatted_time = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                # Determine message direction
                direction = "→" if msg.is_from_me else "←"
                
                # Handle different message types
                media_type = getattr(msg, 'media_type', None)
                
                if not media_type:
                    print(f"{formatted_time} {direction} {msg.content}")
                elif media_type == 'image':
                    print(f"{formatted_time} {direction} [IMAGE] {msg.content}")
                elif media_type == 'video':
                    print(f"{formatted_time} {direction} [VIDEO] {msg.content}")
                elif media_type == 'audio':
                    print(f"{formatted_time} {direction} [AUDIO]")
                elif media_type == 'document':
                    print(f"{formatted_time} {direction} [DOCUMENT] {msg.content}")
                else:
                    print(f"{formatted_time} {direction} [{media_type.upper()}] {msg.content}")
                
                print("-" * 80)
            
            print(f"\nTotal messages: {len(messages)}")
            
        except Exception as e:
            print(f"Error retrieving messages: {e}")
            
    else:
        print("Contact 'Melanie' not found in contacts.json")
