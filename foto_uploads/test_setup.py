#!/usr/bin/env python3
"""
Test and setup script for Step 1 Photo Upload
Validates all components before running the main service
"""

import os
import sys
import sqlite3
import psycopg2
import requests
from pathlib import Path
import json

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_whatsapp_db():
    """Test WhatsApp database connection"""
    print("🔍 Testing WhatsApp database connection...")
    
    db_path = Path(__file__).parent.parent / 'whatsapp-mcp/whatsapp-bridge/store/messages.db'
    
    if not db_path.exists():
        print(f"❌ WhatsApp database not found at: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'messages' not in tables:
            print("❌ Messages table not found")
            return False
            
        # Check for image messages in test groups
        test_groups = [
            '120363418298130331@g.us',  # Lawley
            '120363421664266245@g.us'   # Velo
        ]
        
        for group_jid in test_groups:
            cursor.execute("""
                SELECT COUNT(*) FROM messages 
                WHERE chat_jid = ? AND media_type = 'image'
                LIMIT 5
            """, (group_jid,))
            
            count = cursor.fetchone()[0]
            group_name = 'Lawley' if '1803' in group_jid else 'Velo'
            print(f"📊 {group_name} group: {count} image messages found")
        
        conn.close()
        print("✅ WhatsApp database connection: OK")
        return True
        
    except Exception as e:
        print(f"❌ WhatsApp database error: {e}")
        return False

def test_whatsapp_bridge():
    """Test WhatsApp bridge API"""
    print("🌉 Testing WhatsApp bridge API...")
    
    try:
        # Test basic connectivity
        response = requests.get('http://localhost:8080', timeout=5)
        print("✅ WhatsApp bridge: Responding")
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️  WhatsApp bridge: Not running (this is OK for now)")
        print("   💡 Start with: cd ../whatsapp-mcp/whatsapp-bridge && go run main.go")
        return False
    except Exception as e:
        print(f"❌ WhatsApp bridge error: {e}")
        return False

def test_neon_database():
    """Test Neon PostgreSQL connection"""
    print("🐘 Testing Neon PostgreSQL connection...")
    
    neon_url = os.getenv('NEON_DATABASE_URL')
    if not neon_url:
        print("⚠️  NEON_DATABASE_URL not set (using SQLite fallback)")
        return False
    
    try:
        conn = psycopg2.connect(neon_url)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        conn.close()
        
        print(f"✅ Neon PostgreSQL: Connected ({version[:50]}...)")
        return True
        
    except Exception as e:
        print(f"❌ Neon database error: {e}")
        return False

def test_directory_structure():
    """Test directory structure"""
    print("📁 Testing directory structure...")
    
    base_dir = Path(__file__).parent
    required_dirs = [
        'config',
        'photos/law/incoming',
        'photos/law/processed', 
        'photos/vel/incoming',
        'photos/vel/processed',
        'logs'
    ]
    
    all_good = True
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}: EXISTS")
        else:
            print(f"❌ {dir_path}: MISSING")
            all_good = False
    
    return all_good

def create_sample_config():
    """Create sample configuration files"""
    print("⚙️  Creating sample configuration...")
    
    config_dir = Path(__file__).parent / 'config'
    
    # Sample projects config
    projects_config = {
        "lawley": {
            "name": "Lawley Activation 3",
            "code": "LAW",
            "whatsapp_group": "120363418298130331@g.us",
            "storage_path": "photos/law/",
            "enabled": True
        },
        "velo": {
            "name": "Velo Test",
            "code": "VEL", 
            "whatsapp_group": "120363421664266245@g.us",
            "storage_path": "photos/vel/",
            "enabled": True
        }
    }
    
    with open(config_dir / 'projects.json', 'w') as f:
        json.dump(projects_config, f, indent=2)
    
    print("✅ Sample configuration created")

def run_simple_test():
    """Run a simple test of the photo upload service"""
    print("🧪 Running simple photo upload test...")
    
    try:
        from simple_photo_upload import SimplePhotoUpload
        
        service = SimplePhotoUpload()
        
        # Test getting photos (without processing)
        photos = service.get_new_photos()
        print(f"📸 Found {len(photos)} recent photos in monitored groups")
        
        if photos:
            print("Recent photos:")
            for i, photo in enumerate(photos[:3]):  # Show first 3
                print(f"  {i+1}. {photo['message_id'][:8]}... from {photo['group_name']}")
                if photo['drop_number']:
                    print(f"     Drop: {photo['drop_number']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Step 1 Photo Upload - Setup & Test")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Directory Structure", test_directory_structure),
        ("WhatsApp Database", test_whatsapp_db), 
        ("WhatsApp Bridge", test_whatsapp_bridge),
        ("Neon Database", test_neon_database),
    ]
    
    results = {}
    for test_name, test_func in tests:
        results[test_name] = test_func()
        print()
    
    # Create config
    create_sample_config()
    print()
    
    # Run service test
    results["Service Test"] = run_simple_test()
    print()
    
    # Summary
    print("📊 TEST SUMMARY")
    print("-" * 20)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if results["Directory Structure"] and results["WhatsApp Database"]:
        print("\n🚀 READY TO TEST!")
        print("Run: python simple_photo_upload.py --once")
    else:
        print("\n⚠️  Fix failing tests before proceeding")

if __name__ == "__main__":
    main()