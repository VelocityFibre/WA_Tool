#!/usr/bin/env python3
import sys
import json
import requests
from datetime import datetime

def retrieve_messages_from_melanie():
    """
    Retrieve all messages from Melanie using WhatsApp MCP.
    """
    # Get Melanie's phone number from contacts.json
    try:
        with open('contacts.json', 'r') as f:
            contacts = json.load(f)
            
        phone_number = None
        for contact in contacts:
            if contact['name'].lower() == 'melanie':
                phone_number = contact['number']
                break
                
        if not phone_number:
            print("Melanie not found in contacts.json")
            return
            
        print(f"Found Melanie's phone number: {phone_number}")
        
        # Format JID for WhatsApp
        jid = f"{phone_number}@s.whatsapp.net"
        print(f"WhatsApp JID: {jid}")
        
        # Use WhatsApp MCP to list messages from this contact
        try:
            # First try to get the direct chat
            response = requests.post(
                "http://localhost:8080/api/chat/get-by-contact",
                json={"phone": phone_number}
            )
            
            if response.status_code != 200:
                print(f"Error retrieving chat: {response.status_code}")
                print(response.text)
                return
                
            chat_data = response.json()
            print(f"Chat data: {json.dumps(chat_data, indent=2)}")
            
            # Now list messages from this chat
            response = requests.post(
                "http://localhost:8080/api/messages/list",
                json={
                    "chat_jid": jid,
                    "limit": 100  # Retrieve up to 100 messages
                }
            )
            
            if response.status_code != 200:
                print(f"Error retrieving messages: {response.status_code}")
                print(response.text)
                return
                
            messages = response.json()
            
            if not messages or len(messages) == 0:
                print(f"No messages found from Melanie ({phone_number})")
                return
                
            # Display messages
            print(f"\nMessages from Melanie ({phone_number}):\n")
            print("-" * 80)
            
            for msg in messages:
                # Format timestamp
                timestamp = datetime.fromisoformat(msg.get('timestamp', '').replace('Z', '+00:00'))
                formatted_time = timestamp.strftime('%Y-%m-%d %H:%M:%S')
                
                # Determine message direction
                direction = "→" if msg.get('fromMe', False) else "←"
                
                # Handle different message types
                msg_type = msg.get('type', 'unknown')
                
                if msg_type == 'chat':
                    print(f"{formatted_time} {direction} {msg.get('content', '')}")
                elif msg_type == 'image':
                    print(f"{formatted_time} {direction} [IMAGE] {msg.get('caption', '')}")
                elif msg_type == 'video':
                    print(f"{formatted_time} {direction} [VIDEO] {msg.get('caption', '')}")
                elif msg_type == 'audio':
                    print(f"{formatted_time} {direction} [AUDIO]")
                elif msg_type == 'document':
                    print(f"{formatted_time} {direction} [DOCUMENT] {msg.get('filename', '')}")
                else:
                    print(f"{formatted_time} {direction} [{msg_type.upper()}]")
                
                print("-" * 80)
            
            print(f"\nTotal messages: {len(messages)}")
            
        except Exception as e:
            print(f"Error retrieving messages: {e}")
            
    except Exception as e:
        print(f"Error loading contacts: {e}")

if __name__ == "__main__":
    retrieve_messages_from_melanie()
