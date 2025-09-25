#!/usr/bin/env python3
import os
import sqlite3
import argparse
from datetime import datetime, timedelta

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'whatsapp-mcp/whatsapp-bridge/store/messages.db')
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, '../Airtable/Velocity/fibretime_subbies'))
LOG_FILE = os.path.join(BASE_DIR, 'logs/daily_update.log')
CHAT_JID = '120363417538730975@g.us'  # Velocity/fibretime subbies group JID


def fetch_daily_update(date_str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT content FROM messages
        WHERE chat_jid = ?
          AND content LIKE '%DAILY UPDATE%'
          AND date(timestamp) = ?
        ORDER BY timestamp DESC
        LIMIT 1
        """, (CHAT_JID, date_str)
    )
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


def write_update(content, date_str):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = f"{date_str}_Lawley.txt"
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w') as f:
        f.write(content + '\n')
    return path


def log(entry):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    ts = datetime.now().isoformat()
    with open(LOG_FILE, 'a') as lf:
        lf.write(f"{ts} {entry}\n")


def main():
    parser = argparse.ArgumentParser(description='Extract daily update')
    parser.add_argument('--date', '-d', help='Date to process (YYYY-MM-DD)', default=None)
    args = parser.parse_args()
    date_str = args.date if args.date else datetime.now().strftime('%Y-%m-%d')
    content = fetch_daily_update(date_str)
    if content:
        path = write_update(content, date_str)
        log(f"SUCCESS: wrote update to {path}")
    else:
        log(f"WARNING: no Daily Update found for {date_str}")


if __name__ == '__main__':
    main()
