#!/usr/bin/env python3
"""
Step 1: Simple Photo Upload with QA Info
Requires: Drop number, QA step, saves user and timestamp
"""

import os
import sqlite3
import requests
import shutil
import re
import json
from datetime import datetime
from pathlib import Path

# Simple config
WHATSAPP_DB = Path(__file__).parent.parent / 'whatsapp-mcp/whatsapp-bridge/store/messages.db'
PHOTOS_DIR = Path(__file__).parent / 'photos'
BRIDGE_URL = 'http://localhost:8080'

# Groups to monitor
GROUPS = {
    '120363418298130331@g.us': 'lawley',
    '120363421664266245@g.us': 'velo'
}

# QA Steps mapping (for validation)
QA_STEPS = {
    1: "Property Frontage",
    2: "Location on Wall (Before Install)", 
    3: "Outside Cable Span",
    4: "Home Entry Point – Outside",
    5: "Home Entry Point – Inside",
    6: "Fibre Entry to ONT (After Install)",
    7: "Patched & Labelled Drop",
    8: "Overall Work Area After Completion",
    9: "ONT Barcode – Scan barcode + photo",
    10: "Mini-UPS Serial Number (Gizzu)",
    11: "Powermeter Reading (Drop/Feeder)",
    12: "Powermeter at ONT (Before Activation)",
    13: "Active Broadband Light",
    14: "Customer Signature"
}

def setup():
    """Create directories and log file"""
    for project in GROUPS.values():
        (PHOTOS_DIR / project).mkdir(parents=True, exist_ok=True)
    
    # Create uploads log
    log_file = PHOTOS_DIR / 'uploads.log'
    if not log_file.exists():
        log_file.touch()
    
    print(f"📁 Setup complete: {PHOTOS_DIR}")

def parse_message(content):
    """Parse WhatsApp message for required info"""
    if not content:
        return None
    
    content = content.upper()
    
    # Extract drop number (DR followed by numbers)
    drop_match = re.search(r'\bDR\d+\b', content)
    if not drop_match:
        return None
    
    drop_number = drop_match.group()
    
    # Extract QA step (step X, step X:, X., etc.)
    step_patterns = [
        r'\bSTEP\s*(\d{1,2})\b',
        r'\b(\d{1,2})\.',
        r'\bSTEP\s*(\d{1,2}):'
    ]
    
    qa_step = None
    for pattern in step_patterns:
        step_match = re.search(pattern, content)
        if step_match:
            step_num = int(step_match.group(1))
            if 1 <= step_num <= 14:
                qa_step = step_num
                break
    
    if not qa_step:
        return None
    
    # Extract image sequence number (optional)
    image_seq = 1  # default
    seq_match = re.search(r'\bIMAGE?\s*(\d)\b', content)
    if seq_match:
        image_seq = int(seq_match.group(1))
    
    return {
        'drop_number': drop_number,
        'qa_step': qa_step,
        'image_seq': image_seq,
        'original_content': content
    }

def get_recent_photos():
    """Get recent photos with parsed message content"""
    if not WHATSAPP_DB.exists():
        print(f"❌ WhatsApp database not found: {WHATSAPP_DB}")
        return []
    
    conn = sqlite3.connect(str(WHATSAPP_DB))
    cursor = conn.cursor()
    
    valid_photos = []
    
    # Get images from last 24 hours
    yesterday = int((datetime.now().timestamp() - 86400) * 1000)
    
    for group_jid, project in GROUPS.items():
        cursor.execute("""
            SELECT id, sender, content, filename, timestamp 
            FROM messages 
            WHERE chat_jid = ? 
            AND media_type = 'image' 
            AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 20
        """, (group_jid, yesterday))
        
        for row in cursor.fetchall():
            message_id, sender, content, filename, timestamp = row
            
            # Parse message for required QA info
            parsed = parse_message(content or "")
            if not parsed:
                print(f"⚠️  Skipping {message_id[:8]}: Missing drop number or QA step")
                continue
            
            valid_photos.append({
                'message_id': message_id,
                'group_jid': group_jid,
                'project': project,
                'sender': sender or 'unknown',
                'filename': filename or 'photo.jpg',
                'timestamp': timestamp,
                'drop_number': parsed['drop_number'],
                'qa_step': parsed['qa_step'],
                'image_seq': parsed['image_seq'],
                'content': content
            })
    
    conn.close()
    return valid_photos

def download_photo(message_id, group_jid):
    """Download photo from WhatsApp bridge"""
    try:
        response = requests.post(f"{BRIDGE_URL}/api/download", json={
            'message_id': message_id,
            'chat_jid': group_jid
        }, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return result.get('path')
        
        return None
        
    except Exception as e:
        print(f"❌ Download error {message_id[:8]}: {e}")
        return None

def save_photo(source_path, photo_info):
    """Save photo with QA-specific naming and logging"""
    if not os.path.exists(source_path):
        return None
    
    try:
        # Create organized filename: DR1748808_Step09_Img1_143022.jpg
        timestamp = datetime.now().strftime('%H%M%S')
        drop = photo_info['drop_number']
        step = f"Step{photo_info['qa_step']:02d}"
        img_seq = f"Img{photo_info['image_seq']}"
        _, ext = os.path.splitext(photo_info['filename'])
        
        filename = f"{drop}_{step}_{img_seq}_{timestamp}{ext}"
        
        # Save to project folder
        target_dir = PHOTOS_DIR / photo_info['project']
        target_path = target_dir / filename
        
        shutil.copy2(source_path, target_path)
        
        # Log the upload
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'drop_number': photo_info['drop_number'],
            'qa_step': photo_info['qa_step'],
            'qa_step_name': QA_STEPS.get(photo_info['qa_step'], 'Unknown'),
            'image_sequence': photo_info['image_seq'],
            'user': photo_info['sender'],
            'project': photo_info['project'],
            'message_id': photo_info['message_id'],
            'original_content': photo_info['content']
        }
        
        # Append to log file
        with open(PHOTOS_DIR / 'uploads.log', 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        return str(target_path)
        
    except Exception as e:
        print(f"❌ Save error: {e}")
        return None

def process_photos():
    """Process valid photos with QA information"""
    print("🔍 Looking for photos with QA info (Drop number + Step)...")
    
    photos = get_recent_photos()
    if not photos:
        print("📸 No valid QA photos found")
        print("\n💡 Photos need format like: 'DR1748808 Step 9 ONT barcode photo'")
        return
    
    print(f"📸 Found {len(photos)} valid QA photos")
    
    successful = 0
    for photo in photos:
        qa_step_name = QA_STEPS.get(photo['qa_step'], 'Unknown')
        
        print(f"⬇️  Processing: {photo['drop_number']} Step {photo['qa_step']} ({qa_step_name})")
        print(f"    From: {photo['sender']} in {photo['project']}")
        
        # Download from WhatsApp
        downloaded_path = download_photo(photo['message_id'], photo['group_jid'])
        if not downloaded_path:
            print("    ❌ Download failed")
            continue
        
        # Save with QA info
        saved_path = save_photo(downloaded_path, photo)
        if saved_path:
            filename = os.path.basename(saved_path)
            print(f"    ✅ Saved: {filename}")
            successful += 1
        else:
            print("    ❌ Save failed")
        print()
    
    print(f"🎉 Complete: {successful}/{len(photos)} QA photos processed")
    
    if successful > 0:
        print(f"📊 View upload log: {PHOTOS_DIR}/uploads.log")

def show_example():
    """Show example message formats"""
    print("\n📋 EXAMPLE MESSAGE FORMATS:")
    print("=" * 40)
    print("✅ Valid formats:")
    print("   'DR1748808 Step 1 Property frontage photo'")
    print("   'DR1234567 step 9: ONT barcode scan'")
    print("   'Step 14 customer signature DR9999999'")
    print("   'DR5555555 Step 12 Image 2 power reading'")
    print()
    print("❌ Invalid (will be skipped):")
    print("   'Just a random photo'")
    print("   'DR123456 without step number'")
    print("   'Step 5 without drop number'")

def main():
    print("📸 Simple QA Photo Upload - Step 1")
    print("=" * 50)
    
    setup()
    
    if len(os.sys.argv) > 1 and os.sys.argv[1] == '--examples':
        show_example()
        return
    
    process_photos()
    
    print("\n💡 For message format examples, run: python simple_upload.py --examples")

if __name__ == "__main__":
    main()