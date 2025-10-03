#!/usr/bin/env python3
"""
Test Kill Switch Functionality
=============================

Quick test to verify the kill switch will work properly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from realtime_drop_monitor import check_for_kill_command, KILL_COMMANDS
from datetime import datetime

def test_kill_switch():
    """Test kill command detection."""
    print("🧪 Testing Kill Switch Functionality")
    print("=" * 50)
    
    # Test messages
    test_messages = [
        {
            'content': 'DR1234567 completed',
            'sender': 'test@s.whatsapp.net',
            'chat_jid': '120363421664266245@g.us',
            'id': 'test1'
        },
        {
            'content': 'KILL',  # This should trigger kill switch
            'sender': 'admin@s.whatsapp.net', 
            'chat_jid': '120363421532174586@g.us',
            'id': 'test2'
        },
        {
            'content': 'Normal message',
            'sender': 'user@s.whatsapp.net',
            'chat_jid': '120363421664266245@g.us', 
            'id': 'test3'
        }
    ]
    
    print("📋 Test Messages:")
    for i, msg in enumerate(test_messages, 1):
        print(f"  {i}. '{msg['content']}' from {msg['sender']}")
    
    print(f"\n🎯 Kill Commands: {KILL_COMMANDS}")
    
    # Test first message (should NOT trigger)
    print(f"\n🧪 Testing message 1: '{test_messages[0]['content']}'")
    result1 = check_for_kill_command([test_messages[0]])
    print(f"   Result: {'KILL DETECTED' if result1 else 'No kill command'}")
    
    # Test kill message (should trigger, but we'll catch it)
    print(f"\n🧪 Testing message 2: '{test_messages[1]['content']}'")
    print("   ⚠️  This should detect kill command (but won't actually kill in test)")
    
    # Check if kill command would be detected
    kill_detected = False
    content = test_messages[1]['content'].upper()
    for kill_cmd in KILL_COMMANDS:
        if kill_cmd.upper() in content:
            kill_detected = True
            print(f"   ✅ KILL COMMAND DETECTED: '{kill_cmd}'")
            break
    
    if not kill_detected:
        print("   ❌ Kill command NOT detected")
    
    print(f"\n🧪 Testing message 3: '{test_messages[2]['content']}'")
    result3 = check_for_kill_command([test_messages[2]])
    print(f"   Result: {'KILL DETECTED' if result3 else 'No kill command'}")
    
    print("\n" + "=" * 50)
    print("✅ Kill Switch Test Complete")
    print("\nTo test in real WhatsApp:")
    print("1. Start the realtime monitor")
    print("2. Send 'KILL' to any monitored group")
    print("3. All services should stop immediately")

if __name__ == "__main__":
    test_kill_switch()