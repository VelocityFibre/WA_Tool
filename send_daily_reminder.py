#!/usr/bin/env python3
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'whatsapp-mcp/whatsapp-mcp-server'))
import whatsapp
import sqlite3
from datetime import datetime
import argparse

# Group JID for Velocity/Fibretime subbies
CHAT_JID = '120363417538730975@g.us'

MESSAGE = (
    "VF Ai Agent here,\n\n"
    "Pls remember to send today's daily update summary.\n"
    "If you’ve already sent it, thank you 😊\n\n"
    "Rest well !\n"
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, 'whatsapp-mcp/whatsapp-bridge/store/messages.db')

def send_reminder(dry_run=False):
    # Skip if today's daily update has been sent
    date_str = datetime.now().strftime('%Y-%m-%d')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM messages WHERE chat_jid=? AND content LIKE ? AND date(timestamp)=? LIMIT 1",
        (CHAT_JID, '%DAILY UPDATE%', date_str)
    )
    if cursor.fetchone():
        print(f"Daily update already received for {date_str}; skipping reminder.")
        conn.close()
        return
    conn.close()

    if dry_run:
        print(f"[DRY RUN] Would send reminder to {CHAT_JID} with message:\n{MESSAGE}")
        return
    result, info = whatsapp.send_message(CHAT_JID, MESSAGE)
    print(f"Reminder sent: Success={result}, Info={info}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send daily reminder')
    parser.add_argument('-n','--dry-run', action='store_true', help='Show what would be sent without sending')
    args = parser.parse_args()
    send_reminder(dry_run=args.dry_run)
