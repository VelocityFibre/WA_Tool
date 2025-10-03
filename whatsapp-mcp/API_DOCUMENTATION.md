# API Documentation - WhatsApp Quality Control System

## Overview

This document provides comprehensive API documentation for the WhatsApp Quality Control System, including both the core WhatsApp MCP tools and the Quality Assurance Photo Review System.

## 🔧 MCP Tools (WhatsApp Integration)

### Contact Management

#### `search_contacts`
Search for contacts by name or phone number.
```python
# Usage in Claude
search_contacts(query="John")
search_contacts(query="+27812345678")
```

**Parameters:**
- `query` (string): Contact name or phone number to search for

**Returns:**
- List of contacts with name, phone number, and JID

#### `get_contact_chats`
List all chats involving a specific contact.
```python
get_contact_chats(contact_jid="27812345678@s.whatsapp.net")
```

### Chat Management

#### `list_chats`
List available chats with metadata.
```python
list_chats(limit=50)
```

**Parameters:**
- `limit` (optional): Maximum number of chats to return

**Returns:**
- List of chats with JID, name, last message time, and participant count

#### `get_chat`
Get detailed information about a specific chat.
```python
get_chat(chat_jid="120363418298130331@g.us")
```

#### `get_direct_chat_by_contact`
Find a direct chat with a specific contact.
```python
get_direct_chat_by_contact(contact_jid="27812345678@s.whatsapp.net")
```

### Message Management

#### `list_messages`
Retrieve messages with optional filters and context.
```python
list_messages(
    chat_jid="120363418298130331@g.us",
    limit=100,
    search_term="DR1748808",
    include_context=True
)
```

**Parameters:**
- `chat_jid` (string): Chat identifier
- `limit` (optional): Maximum number of messages
- `search_term` (optional): Filter messages containing this text
- `include_context` (optional): Include surrounding message context

#### `get_message_context`
Retrieve context around a specific message.
```python
get_message_context(
    message_id="ACAA576FFD6C19B4C83172230C833DDC",
    chat_jid="120363418298130331@g.us",
    context_size=5
)
```

#### `get_last_interaction`
Get the most recent message with a contact.
```python
get_last_interaction(contact_jid="27812345678@s.whatsapp.net")
```

### Message Sending

#### `send_message`
Send a WhatsApp message to a specified recipient.
```python
send_message(
    recipient="120363418298130331@g.us",  # Group JID
    message="Installation completed for DR1748808"
)

send_message(
    recipient="27812345678",  # Phone number
    message="Quality review ready for DR1740820"
)
```

#### `send_file`
Send a file (image, video, document) to a specified recipient.
```python
send_file(
    recipient="27812345678@s.whatsapp.net",
    file_path="/path/to/installation_photo.jpg",
    caption="ONT installation complete"
)
```

**Supported file types:**
- Images: JPG, PNG, WebP
- Videos: MP4, AVI, MOV
- Documents: PDF, DOC, XLS, etc.
- Raw audio files

#### `send_audio_message`
Send an audio file as a WhatsApp voice message.
```python
send_audio_message(
    recipient="27812345678@s.whatsapp.net",
    audio_path="/path/to/voice_note.ogg"
)
```

**Requirements:**
- Audio must be in .ogg Opus format for optimal compatibility
- FFmpeg automatically converts other formats if installed

### Media Handling

#### `download_media`
Download and access media files from WhatsApp messages.
```python
download_media(
    message_id="ACAA576FFD6C19B4C83172230C833DDC",
    chat_jid="120363418298130331@g.us"
)
```

**Returns:**
- Local file path where media was downloaded
- File metadata (type, size, original filename)

## 🎯 Quality Control API

### Installation Records

#### GET `/api/installations`
Retrieve installation records with filtering options.

```bash
# Get all installations
curl http://localhost:3000/api/installations

# Filter by status
curl http://localhost:3000/api/installations?status=submitted

# Filter by contractor
curl http://localhost:3000/api/installations?contractor=WhatsApp-80333605232852
```

**Response:**
```json
[
  {
    "id": 26,
    "drop_number": "DR1748808",
    "contractor_name": "WhatsApp-80333605232852",
    "customer_name": null,
    "address": "Extracted from WhatsApp Lawley Activation 3 group",
    "status": "submitted",
    "completion_percentage": 0,
    "date_submitted": "2025-09-26T08:47:36.355Z",
    "agent_notes": "Auto-imported from WhatsApp...",
    "created_at": "2025-09-26T08:47:36.355Z"
  }
]
```

#### POST `/api/installations`
Create a new installation record.

```bash
curl -X POST http://localhost:3000/api/installations \
  -H "Content-Type: application/json" \
  -d '{
    "drop_number": "DR1750123",
    "contractor_name": "John Smith Contractors",
    "customer_name": "Jane Doe",
    "address": "123 Main Street, Cape Town",
    "ont_barcode": "ONT123456789",
    "ups_serial_number": "UPS987654321"
  }'
```

### QA Photo Reviews

#### GET `/api/qa-photos`
Retrieve QA photo reviews with filtering options.

```bash
# Get all QA reviews
curl http://localhost:3000/api/qa-photos

# Filter by user/reviewer
curl http://localhost:3000/api/qa-photos?user=80333605232852

# Filter by date range
curl http://localhost:3000/api/qa-photos?startDate=2025-09-25&endDate=2025-09-26
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "drop_number": "DR1748808",
    "review_date": "2025-09-26",
    "user_name": "80333605232852",
    "step_01_property_frontage": false,
    "step_02_location_before_install": false,
    "step_03_outside_cable_span": false,
    "step_04_home_entry_outside": false,
    "step_05_home_entry_inside": false,
    "step_06_fibre_entry_to_ont": false,
    "step_07_patched_labelled_drop": false,
    "step_08_work_area_completion": false,
    "step_09_ont_barcode_scan": false,
    "step_10_ups_serial_number": false,
    "step_11_powermeter_reading": false,
    "step_12_powermeter_at_ont": false,
    "step_13_active_broadband_light": false,
    "step_14_customer_signature": false,
    "completed_photos": 0,
    "outstanding_photos": 14,
    "outstanding_photos_loaded_to_1map": false,
    "comment": "Auto-created from WhatsApp drop detection",
    "created_at": "2025-09-26T08:47:36.355Z",
    "updated_at": "2025-09-26T08:47:36.355Z"
  }
]
```

#### POST `/api/qa-photos`
Create a new QA photo review.

```bash
curl -X POST http://localhost:3000/api/qa-photos \
  -H "Content-Type: application/json" \
  -d '{
    "drop_number": "DR1750123",
    "user_name": "JohnSmith",
    "review_date": "2025-09-26",
    "step_01_property_frontage": true,
    "step_02_location_before_install": true,
    "comment": "Initial review - property and location photos completed"
  }'
```

#### PUT `/api/qa-photos`
Update an existing QA photo review.

```bash
# Update a specific QA step
curl -X PUT http://localhost:3000/api/qa-photos \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "step_03_outside_cable_span": true
  }'

# Update comment
curl -X PUT http://localhost:3000/api/qa-photos \
  -H "Content-Type: application/json" \
  -d '{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "comment": "Cable span photo now complete - good quality"
  }'
```

## 🔄 System Status & Monitoring API

### GET `/api/system-status`
Retrieve comprehensive real-time system health status including all components, databases, and monitoring state.

```bash
# Get full system status
curl http://localhost:3000/api/system-status | jq

# Quick health check
curl -s http://localhost:3000/api/system-status | jq '.overall'

# Component-specific status
curl -s http://localhost:3000/api/system-status | jq '.services'
```

**Response:**
```json
{
  "timestamp": "2025-09-26T10:05:07.123Z",
  "overall": "healthy",
  "services": {
    "whatsapp-bridge": {
      "description": "WhatsApp Bridge (Go)",
      "status": "active",
      "active": true,
      "systemd": {
        "type": "systemd",
        "active": false,
        "status": "not-installed",
        "error": "Service not found"
      },
      "process": {
        "type": "process",
        "active": true,
        "status": "running",
        "processCount": 1,
        "processes": [
          {
            "pid": "184136",
            "cpu": "0.0",
            "memory": "0.0",
            "command": "./whatsapp-bridge"
          }
        ]
      },
      "lastCheck": "2025-09-26T10:05:07.123Z"
    },
    "whatsapp-mcp": {
      "description": "MCP Server (Python)",
      "status": "active",
      "active": true,
      "systemd": {
        "type": "systemd",
        "active": false,
        "status": "not-installed",
        "error": "Service not found"
      },
      "process": {
        "type": "process",
        "active": true,
        "status": "running",
        "processCount": 2,
        "processes": [
          {
            "pid": "136786",
            "cpu": "0.0",
            "memory": "0.0",
            "command": "uv run main.py"
          },
          {
            "pid": "136791",
            "cpu": "0.0",
            "memory": "0.1",
            "command": "/path/to/.venv/bin/python3 main.py"
          }
        ]
      },
      "lastCheck": "2025-09-26T10:05:07.123Z"
    },
    "whatsapp-drop-monitor": {
      "description": "Drop Monitor (Python)",
      "status": "active",
      "active": true,
      "systemd": {
        "type": "systemd",
        "active": true,
        "status": "active"
      },
      "process": {
        "type": "process",
        "active": true,
        "status": "running",
        "processCount": 2,
        "processes": [
          {
            "pid": "192845",
            "cpu": "0.0",
            "memory": "0.0",
            "command": "/home/user/.local/bin/uv run python realtime_drop_monitor.py --interval 15"
          }
        ]
      },
      "lastCheck": "2025-09-26T10:05:07.123Z"
    }
  },
  "database": {
    "neon": {
      "status": "connected",
      "responsive": true,
      "lastQuery": "2025-09-26T10:05:07.123Z",
      "recordCount": 1
    },
    "overall": "healthy"
  },
  "whatsapp": {
    "database": {
      "exists": true,
      "size": 2097152,
      "lastModified": "2025-09-26T09:49:38.000Z",
      "recentMessages": 70,
      "latestMessage": "2025-09-26 11:49:38+02:00"
    },
    "authentication": {
      "status": "unknown",
      "lastAuth": null
    },
    "status": "active",
    "lastCheck": "2025-09-26T10:05:07.123Z"
  },
  "monitor": {
    "state": {
      "lastCheckTime": "2025-09-26T11:58:03.807755",
      "processedMessages": 0,
      "savedAt": "2025-09-26T11:58:03.807775",
      "minutesSinceLastCheck": 1,
      "isActive": true
    },
    "status": "active",
    "lastStateUpdate": "2025-09-26T10:05:07.123Z"
  }
}
```

#### Status Levels
- **`healthy`**: All systems operational, databases responsive
- **`warning`**: Some components have issues but core functionality working
- **`error`**: Critical systems offline or major connectivity problems

#### Component Status Detection
The API uses a hybrid approach to detect service status:
1. **Systemd Services**: Checks `systemctl is-active` for installed services
2. **Process Detection**: Uses `ps aux | grep` to find running processes
3. **Hybrid Logic**: Component shows as "active" if either systemd OR process is running

#### Usage in Frontend
This endpoint is consumed by:
- **Header Status Indicator**: Auto-refreshes every 60 seconds
- **System Monitor Dashboard**: Detailed view with 30-second refresh
- **Manual Refresh**: Instant updates via "Refresh Now" button

## 🔄 Real-time Monitor API

The real-time monitor doesn't expose HTTP endpoints but provides programmatic interfaces:

### Monitor State Management

#### Get Current State
```python
import json

# Read current monitor state
with open('monitor_state.json', 'r') as f:
    state = json.load(f)
    
print(f"Last check: {state['last_check_time']}")
print(f"Processed IDs: {len(state['processed_message_ids'])}")
```

#### Update State
```python
import json
from datetime import datetime

# Update monitor state
state = {
    "last_check_time": datetime.now().isoformat(),
    "processed_message_ids": ["MSG1", "MSG2"],
    "saved_at": datetime.now().isoformat()
}

with open('monitor_state.json', 'w') as f:
    json.dump(state, f, indent=2)
```

### Drop Number Processing

#### Manual Drop Processing
```python
# Process a specific drop number manually
from realtime_drop_monitor import create_qa_photo_review, insert_drop_numbers_to_neon

drop_data = [{
    'drop_number': 'DR1750123',
    'contractor_name': 'WhatsApp-80333605232852',
    'message_id': 'MSG123',
    'sender': '80333605232852',
    'timestamp': datetime.now(),
    'message_content': 'Installation complete DR1750123',
    'address': 'Extracted from WhatsApp Lawley Activation 3 group'
}]

# Create installation record and QA review
result = insert_drop_numbers_to_neon(drop_data, dry_run=False)
```

## 📊 Database Schema

### Installations Table
```sql
CREATE TABLE installations (
    id SERIAL PRIMARY KEY,
    drop_number VARCHAR(50) NOT NULL UNIQUE,
    contractor_name VARCHAR(255),
    customer_name VARCHAR(255),
    address TEXT,
    status VARCHAR(50) DEFAULT 'submitted',
    completion_percentage INTEGER DEFAULT 0,
    date_submitted TIMESTAMP DEFAULT NOW(),
    date_reviewed TIMESTAMP,
    reviewed_by VARCHAR(255),
    agent_notes TEXT,
    ont_barcode VARCHAR(255),
    ups_serial_number VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### QA Photo Reviews Table
```sql
CREATE TABLE qa_photo_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    drop_number VARCHAR(50) NOT NULL,
    review_date DATE NOT NULL DEFAULT CURRENT_DATE,
    user_name VARCHAR(100) NOT NULL,
    
    -- 14 QA step fields (boolean)
    step_01_property_frontage BOOLEAN DEFAULT FALSE,
    step_02_location_before_install BOOLEAN DEFAULT FALSE,
    step_03_outside_cable_span BOOLEAN DEFAULT FALSE,
    step_04_home_entry_outside BOOLEAN DEFAULT FALSE,
    step_05_home_entry_inside BOOLEAN DEFAULT FALSE,
    step_06_fibre_entry_to_ont BOOLEAN DEFAULT FALSE,
    step_07_patched_labelled_drop BOOLEAN DEFAULT FALSE,
    step_08_work_area_completion BOOLEAN DEFAULT FALSE,
    step_09_ont_barcode_scan BOOLEAN DEFAULT FALSE,
    step_10_ups_serial_number BOOLEAN DEFAULT FALSE,
    step_11_powermeter_reading BOOLEAN DEFAULT FALSE,
    step_12_powermeter_at_ont BOOLEAN DEFAULT FALSE,
    step_13_active_broadband_light BOOLEAN DEFAULT FALSE,
    step_14_customer_signature BOOLEAN DEFAULT FALSE,
    
    -- Auto-calculated summary fields
    completed_photos INTEGER GENERATED ALWAYS AS (
        (CASE WHEN step_01_property_frontage THEN 1 ELSE 0 END) +
        (CASE WHEN step_02_location_before_install THEN 1 ELSE 0 END) +
        -- ... (sum of all 14 steps)
        (CASE WHEN step_14_customer_signature THEN 1 ELSE 0 END)
    ) STORED,
    
    outstanding_photos INTEGER GENERATED ALWAYS AS (
        14 - completed_photos
    ) STORED,
    
    outstanding_photos_loaded_to_1map BOOLEAN DEFAULT FALSE,
    comment TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure unique entry per drop number and date
    UNIQUE(drop_number, review_date)
);
```

## 🔐 Authentication & Security

### WhatsApp Authentication
- **QR Code Authentication**: Initial setup requires scanning QR code
- **Session Management**: Sessions persist ~20 days before re-authentication
- **Device Limits**: WhatsApp enforces device connection limits

### Database Security
- **SSL/TLS Connections**: All database connections encrypted
- **Local SQLite**: WhatsApp messages stored locally
- **Access Control**: API requires local network access

### API Security
- **Local Access Only**: APIs bound to localhost
- **No Authentication**: Suitable for local development/internal use
- **Input Validation**: All inputs validated and sanitized

## 📈 Performance & Rate Limits

### WhatsApp API Limits
- **Message Sending**: ~100 messages per hour (varies by account)
- **Media Upload**: Limited by file size and connection speed
- **Authentication**: QR code expires after ~60 seconds

### Database Performance
- **Connection Pooling**: Efficient database connection management
- **Indexing**: Optimized indexes for common queries
- **Batch Processing**: Multiple operations batched for efficiency

### Real-time Monitor
- **Check Interval**: 15 seconds (configurable)
- **Memory Usage**: ~50MB for monitoring process
- **CPU Usage**: Minimal (<1% average)

## 🔧 Error Handling

### Common Error Responses

#### 400 Bad Request
```json
{
  "error": "Invalid drop number format",
  "details": "Drop number must match pattern DR\\d+"
}
```

#### 404 Not Found
```json
{
  "error": "QA photo review not found",
  "details": "No review found with the specified ID"
}
```

#### 409 Conflict
```json
{
  "error": "QA review already exists for this drop number and date",
  "details": "Use PUT method to update existing review"
}
```

#### 500 Internal Server Error
```json
{
  "error": "Database connection failed",
  "details": "Unable to connect to Neon PostgreSQL database"
}
```

### WhatsApp-Specific Errors
- **Authentication Required**: QR code scan needed
- **Device Limit Reached**: Too many linked devices
- **Message Send Failed**: Network or account restrictions
- **Media Download Failed**: File no longer available

## 📞 API Support

For API-related support:

1. **Check Service Status**: Verify all components are running
2. **Review Logs**: Check application logs for detailed errors
3. **Database Connection**: Test database connectivity
4. **Rate Limits**: Verify you're within WhatsApp rate limits
5. **Authentication**: Ensure WhatsApp session is active

## 🚀 Future API Enhancements

Planned API improvements:
- **Webhook Support**: Real-time notifications for new drop numbers
- **Batch Operations**: Process multiple installations simultaneously
- **Photo Upload API**: Direct photo upload to QA reviews
- **Advanced Filtering**: Complex query support for installations
- **Export APIs**: Generate reports and export data
- **Mobile API**: Optimized endpoints for mobile applications

This API documentation provides comprehensive coverage of all available endpoints and tools in the WhatsApp Quality Control System.