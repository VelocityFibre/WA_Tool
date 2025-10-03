#!/usr/bin/env python3
"""
Script to extract drop numbers from Lawley Activation 3 WhatsApp group.
Usage: uv run python extract_drops.py [--days N] [--today] [--csv]
"""

import argparse
import re
import json
from datetime import datetime, timedelta
from whatsapp import list_messages

# Lawley Activation 3 group JID
LAWLEY_GROUP_JID = '120363418298130331@g.us'

def extract_drop_numbers(days=7, today_only=False, output_format='text'):
    """Extract drop numbers from the Lawley Activation 3 group."""
    
    print(f"Extracting drop numbers from Lawley Activation 3 group...")
    
    # Set date filter
    if today_only:
        after_date = datetime.now().date().isoformat()
        print(f"Filter: Today only ({after_date})")
    else:
        after_date = (datetime.now() - timedelta(days=days)).isoformat()
        print(f"Filter: Last {days} days (since {after_date})")
    
    # Get messages containing DR
    messages = list_messages(
        chat_jid=LAWLEY_GROUP_JID, 
        query='DR', 
        after=after_date, 
        limit=200
    )
    
    # Extract drop numbers using regex
    drop_pattern = r'DR\d+'
    found_drops = {}  # Use dict to store drop with latest timestamp
    
    # Split the messages string by lines and process each line
    message_lines = messages.split('\n')
    
    for line in message_lines:
        # Find all drop numbers in this line
        drops_in_line = re.findall(drop_pattern, line, re.IGNORECASE)
        
        for drop in drops_in_line:
            drop_upper = drop.upper()
            
            # Extract timestamp and sender info
            timestamp_match = re.search(r'\[([\d\-\s:]+)\]', line)
            sender_match = re.search(r'From:\s*([^:]+):', line)
            
            timestamp = timestamp_match.group(1) if timestamp_match else 'Unknown time'
            sender = sender_match.group(1) if sender_match else 'Unknown sender'
            
            # Keep the latest occurrence of each drop number
            if drop_upper not in found_drops or timestamp > found_drops[drop_upper]['timestamp']:
                found_drops[drop_upper] = {
                    'drop': drop_upper,
                    'timestamp': timestamp,
                    'sender': sender,
                    'full_line': line.strip()
                }
    
    # Sort drops by timestamp (most recent first)
    sorted_drops = sorted(found_drops.values(), key=lambda x: x['timestamp'], reverse=True)
    
    # Output results based on format
    if output_format == 'json':
        result = {
            'extraction_date': datetime.now().isoformat(),
            'filter_days': days if not today_only else 0,
            'today_only': today_only,
            'total_unique_drops': len(sorted_drops),
            'drop_numbers': [item['drop'] for item in sorted_drops],
            'detailed_drops': sorted_drops
        }
        print(json.dumps(result, indent=2))
        
    elif output_format == 'csv':
        print("Drop Number,Timestamp,Sender")
        for item in sorted_drops:
            print(f"{item['drop']},{item['timestamp']},{item['sender']}")
            
    else:  # text format (default)
        period = "TODAY" if today_only else f"LAST {days} DAYS"
        print(f"\n{'='*70}")
        print(f"DROP NUMBERS FROM LAWLEY ACTIVATION 3 GROUP ({period})")
        print(f"{'='*70}")
        
        if not sorted_drops:
            print("No drop numbers found.")
        else:
            print(f"Found {len(sorted_drops)} unique drop numbers:\n")
            
            for item in sorted_drops:
                print(f"• {item['drop']} - {item['timestamp']} - From: {item['sender']}")
            
            print(f"\n{'='*70}")
            print("SUMMARY - Drop numbers for grid update:")
            drop_list = [item['drop'] for item in sorted_drops]
            print(f"Total: {len(drop_list)}")
            print("Comma-separated: " + ', '.join(drop_list))
            print("Line-separated:")
            for drop in drop_list:
                print(f"  {drop}")

def main():
    parser = argparse.ArgumentParser(description='Extract drop numbers from Lawley Activation 3 WhatsApp group')
    parser.add_argument('--days', type=int, default=7, 
                       help='Number of days to look back (default: 7)')
    parser.add_argument('--today', action='store_true', 
                       help='Only get today\'s drop numbers')
    parser.add_argument('--format', choices=['text', 'json', 'csv'], default='text',
                       help='Output format (default: text)')
    
    args = parser.parse_args()
    
    extract_drop_numbers(
        days=args.days, 
        today_only=args.today, 
        output_format=args.format
    )

if __name__ == "__main__":
    main()