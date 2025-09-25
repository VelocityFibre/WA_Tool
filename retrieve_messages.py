#!/usr/bin/env python3
import sys
import json
import requests
from datetime import datetime

def retrieve_messages_from_contact(contact_name=None, phone_number=None):
    """
    Retrieve all messages from a specific contact using WhatsApp MCP.
    
    Args:
        contact_name: Name of the contact to retrieve messages from
        phone_number: Phone number of the contact to retrieve messages from
    """
    # Load contacts from contacts.json
    try:
        with open('contacts.json', 'r') as f:
            contacts = json.load(f)
    except Exception as e:
        print(f"Error loading contacts: {e}")
        return
    
    # If contact_name is provided, find the corresponding phone number
    if contact_name and not phone_number:
        for contact in contacts:
            if contact['name'].lower() == contact_name.lower():
                phone_number = contact['number']
                break
        if not phone_number:
            print(f"Contact '{contact_name}' not found in contacts.json")
            return
    
    # Format JID for WhatsApp
    jid = f"{phone_number}@s.whatsapp.net"
    
    # Use MCP to list messages from this contact
    try:
        # First get the chat to ensure it exists
        response = requests.post(
            "http://localhost:8000/tools/get_direct_chat_by_contact",
            json={"sender_phone_number": phone_number}
        )
        
        if response.status_code != 200:
            print(f"Error retrieving chat: {response.status_code}")
            print(response.text)
            return
        
        chat_data = response.json()
        if not chat_data or 'success' in chat_data and not chat_data['success']:
            print(f"No chat found for contact with phone number {phone_number}")
            return
        
        # Now list messages from this chat
        response = requests.post(
            "http://localhost:8000/tools/list_messages",
            json={
                "sender_phone_number": phone_number,
                "limit": 100,  # Retrieve up to 100 messages
                "include_context": False  # We only want messages from this contact
            }
        )
        
        if response.status_code != 200:
            print(f"Error retrieving messages: {response.status_code}")
            print(response.text)
            return
        
        messages = response.json()
        
        if not messages:
            print(f"No messages found from {contact_name or phone_number}")
            return
        
        # Display messages
        print(f"\nMessages from {contact_name or phone_number} ({phone_number}):\n")
        print("-" * 80)
        
        for msg in messages:
            # Format timestamp
            timestamp = datetime.fromisoformat(msg['timestamp'].replace('Z', '+00:00'))
            formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            # Determine message direction
            direction = "→" if msg['from_me'] else "←"
            
            # Handle different message types
            if msg['type'] == 'chat':
                print(f"{formatted_time} {direction} {msg['content']}")
            elif msg['type'] == 'image':
                print(f"{formatted_time} {direction} [IMAGE] {msg.get('caption', '')}")
            elif msg['type'] == 'video':
                print(f"{formatted_time} {direction} [VIDEO] {msg.get('caption', '')}")
            elif msg['type'] == 'audio':
                print(f"{formatted_time} {direction} [AUDIO]")
            elif msg['type'] == 'document':
                print(f"{formatted_time} {direction} [DOCUMENT] {msg.get('filename', '')}")
            else:
                print(f"{formatted_time} {direction} [{msg['type'].upper()}]")
            
            print("-" * 80)
        
        print(f"\nTotal messages: {len(messages)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        contact_name = sys.argv[1]
        retrieve_messages_from_contact(contact_name=contact_name)
    else:
        print("Usage: python retrieve_messages.py <contact_name>")
        print("Example: python retrieve_messages.py Melanie")
