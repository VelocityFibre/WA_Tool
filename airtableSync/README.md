# WhatsApp Daily Update Automation System

## Project Overview

This project automates the collection and management of daily project updates from the "Velocity / fibretime subbies" WhatsApp group, ensuring these updates are properly captured for Airtable integration.

## Project Location

- **Base Directory**: `/home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/`
- **WhatsApp MCP**: `/home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/whatsapp-mcp/`
- **Output Directory**: `/home/ldp/louisdup/Clients/VelocityFibre/Agents/Airtable/Velocity/fibretime_subbies/`
- **Log Directory**: `/home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/logs/`

## Components & Functionality

### 1. WhatsApp Message Monitoring
- **Technology**: WhatsApp MCP (Model Context Protocol) server
- **Database**: SQLite database at `whatsapp-mcp/whatsapp-bridge/store/messages.db`
- **Target Group**: "Velocity / fibretime subbies" (JID: `120363417538730975@g.us`)
- **What It Does**: Continuously captures and stores all WhatsApp messages from the group

### 2. Daily Update Extraction System
- **Script**: `extract_daily_update.py`
- **Schedule**: Daily at 21:30 via crontab
- **Functionality**:
  - Connects to the WhatsApp SQLite database
  - Searches for messages containing "DAILY UPDATE" from today's date
  - Extracts the complete update message with all metrics (pole permissions, etc.)
  - Saves it as a text file named `YYYY-MM-DD_Lawley.txt` in the output directory
  - Logs success or failure to `logs/daily_update.log`
- **Purpose**: Creates standardized text files for Airtable integration

### 3. Reminder System
- **Script**: `send_daily_reminder.py`
- **Schedule**: Monday-Friday at 20:30 via crontab (excludes weekends)
- **Functionality**:
  - Checks if today's "DAILY UPDATE" message exists in the database
  - If no update found, sends a reminder message to the WhatsApp group:
    ```
    VF Ai Agent here,

    Pls remember to send today's daily update summary.
    If you've already sent it, thank you 😊

    Rest well !
    ```
  - If update already exists, skips sending the reminder
  - Logs all actions
- **Purpose**: Ensures timely submission of daily updates

## Technical Implementation

### Database Query Logic
Both scripts query the SQLite database using:
```sql
SELECT content FROM messages 
WHERE chat_jid = '120363417538730975@g.us' 
  AND content LIKE '%DAILY UPDATE%' 
  AND date(timestamp) = '2025-05-16'
```

### File Format
The extracted updates follow this standardized format:
```
❗* DAILY UPDATE - Project: Lawley*  📅 [15-05-25]    ✅ * Agenda: *
1.	Pole Permissions Today – 0
2.	Pole Permissions Total – 475
...
12.	Stringing Total – 0

📌 Comments - No new update. There was no activity on site today due to SMME's stopping the teams
```

### Cron Jobs
Two separate cron jobs have been configured:
```
30 20 * * 1-5 /usr/bin/python3 /home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/send_daily_reminder.py
30 21 * * * /usr/bin/python3 /home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/extract_daily_update.py
```

## Benefits
- **Automation**: Eliminates manual copying of daily updates
- **Consistency**: Ensures standardized format for Airtable integration
- **Reliability**: Reminder system reduces missed updates
- **Audit Trail**: Logging provides visibility into system operation

This system bridges WhatsApp communications with your Airtable-based project management, ensuring critical daily updates are captured, standardized, and ready for further processing.
