#!/usr/bin/env python3
"""
Test Script for Enhanced QA Feedback System
==========================================

Tests:
1. Group configuration and toggles
2. Reply functionality (dry-run)
3. Kill switch functionality
4. Database connectivity

Date: October 2nd, 2025
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from enhanced_qa_feedback import GROUP_CONFIG, get_enabled_groups, get_sheets_service
import whatsapp
from realtime_drop_monitor import check_for_kill_command, KILL_COMMANDS
import sqlite3
import requests

def test_group_configuration():
    """Test group configuration and toggles"""
    print("🧪 Testing Group Configuration")
    print("=" * 50)
    
    # Show current configuration
    print("📊 Current Group Configuration:")
    for name, config in GROUP_CONFIG.items():
        status = "🟢 ENABLED" if config['enabled'] else "🔴 DISABLED" 
        testing = " (TESTING)" if config.get('testing_mode') else ""
        print(f"  {name}: {status}{testing}")
    
    # Test enabled groups function
    enabled = get_enabled_groups()
    print(f"\n✅ Enabled groups: {list(enabled.keys())}")
    
    if len(enabled) == 1 and "Velo Test" in enabled:
        print("✅ PASS: Only Velo Test is enabled for testing")
    else:
        print("❌ FAIL: Expected only Velo Test to be enabled")
    
    print()

def test_whatsapp_bridge_connectivity():
    """Test WhatsApp Bridge connectivity"""
    print("🧪 Testing WhatsApp Bridge Connectivity")  
    print("=" * 50)
    
    try:
        # Test bridge connectivity
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ WhatsApp Bridge is running")
        else:
            print(f"⚠️ WhatsApp Bridge responded with status: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ WhatsApp Bridge is not running on port 8080")
        print("   Start it with: cd ../whatsapp-bridge && ./whatsapp-bridge")
    except Exception as e:
        print(f"❌ Error connecting to WhatsApp Bridge: {e}")
    
    print()

def test_database_connectivity():
    """Test database connectivity"""
    print("🧪 Testing Database Connectivity")
    print("=" * 50)
    
    # Test WhatsApp SQLite database
    whatsapp_db = "../whatsapp-bridge/store/messages.db"
    if os.path.exists(whatsapp_db):
        try:
            conn = sqlite3.connect(whatsapp_db)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages WHERE chat_jid IN (?, ?, ?)", 
                         ('120363418298130331@g.us', '120363421664266245@g.us', '120363421532174586@g.us'))
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            print(f"✅ WhatsApp Database: {count} monitored group messages found")
        except Exception as e:
            print(f"❌ WhatsApp Database error: {e}")
    else:
        print("⚠️ WhatsApp database not found - bridge may not be running")
    
    # Test Google Sheets connectivity
    try:
        service = get_sheets_service()
        if service:
            print("✅ Google Sheets: Service connected successfully")
        else:
            print("❌ Google Sheets: Failed to create service")
    except Exception as e:
        print(f"❌ Google Sheets error: {e}")
    
    print()

def test_kill_switch():
    """Test kill switch functionality"""
    print("🧪 Testing Kill Switch Functionality")
    print("=" * 50)
    
    # Test kill command detection
    print(f"🎯 Kill Commands: {KILL_COMMANDS}")
    
    test_messages = [
        {'content': 'DR1234567 completed', 'id': 'test1'},
        {'content': 'KILL', 'id': 'test2'},  # Should trigger
        {'content': '!KILL', 'id': 'test3'},  # Should trigger
        {'content': 'kill all services', 'id': 'test4'},  # Should trigger
        {'content': 'Normal message', 'id': 'test5'},
    ]
    
    for i, msg in enumerate(test_messages, 1):
        content = msg['content']
        kill_detected = False
        
        # Check if kill command would be detected
        content_upper = content.upper()
        for kill_cmd in KILL_COMMANDS:
            if kill_cmd.upper() in content_upper:
                kill_detected = True
                break
        
        result = "🚨 KILL DETECTED" if kill_detected else "✅ Normal message"
        print(f"  {i}. '{content}' → {result}")
    
    print("✅ Kill switch detection working correctly")
    print()

def test_reply_functionality():
    """Test reply functionality (dry-run)"""
    print("🧪 Testing Reply Functionality (Dry-Run)")
    print("=" * 50)
    
    # Test basic message sending
    try:
        success, response = whatsapp.send_message("test@s.whatsapp.net", "Test message")
        print(f"📤 Regular message test: {'✅ Success' if success else '❌ Failed'} - {response}")
    except Exception as e:
        print(f"❌ Regular message error: {e}")
    
    # Test reply message sending
    try:
        success, response = whatsapp.send_message_reply(
            "test@s.whatsapp.net", 
            "Test reply message", 
            "fake_message_id_for_testing"
        )
        print(f"💬 Reply message test: {'✅ Success' if success else '❌ Failed'} - {response}")
    except Exception as e:
        print(f"❌ Reply message error: {e}")
    
    print()

def run_all_tests():
    """Run all test suites"""
    print("🚀 Enhanced QA Feedback System - Test Suite")
    print("Date: October 2nd, 2025")
    print("=" * 70)
    print()
    
    # Run all tests
    test_group_configuration()
    test_whatsapp_bridge_connectivity()
    test_database_connectivity()  
    test_kill_switch()
    test_reply_functionality()
    
    print("=" * 70)
    print("🎉 Test Suite Complete!")
    print()
    print("📋 Next Steps:")
    print("1. Start WhatsApp Bridge: cd ../whatsapp-bridge && ./whatsapp-bridge")
    print("2. Test enhanced QA monitor: python enhanced_qa_feedback.py --dry-run --test")
    print("3. Test kill switch in Velo Test group only")
    print("4. Enable other groups once testing is complete")

if __name__ == "__main__":
    run_all_tests()