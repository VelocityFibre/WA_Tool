# Project-Specific API Endpoints

## Overview

The WhatsApp Assistant Tool now supports project-based tracking and separate spaces for different WhatsApp groups. This document describes the new API endpoints available for frontend integration.

## Database Schema Changes

The `chats` table now includes a `project_name` column:

```sql
CREATE TABLE chats (
    jid TEXT PRIMARY KEY,
    name TEXT,
    last_message_time TIMESTAMP,
    project_name TEXT
);
```

## Current Projects

- **Lawley**: `120363418298130331@g.us` (Lawley Activation 3 group)
- **Velo Test**: `120363421664266245@g.us` (Velo Test group)

**Note**: Individual contacts and non-project groups are NOT tracked in this system. Only the specific WhatsApp groups listed above are monitored for drop numbers and quality control.

## New API Endpoints

### 1. Get All Projects
**GET** `/api/projects`

Returns all available projects with chat counts.

```json
{
    "success": true,
    "projects": [
        {
            "name": "Lawley", 
            "chat_count": 1
        },
        {
            "name": "Velo Test",
            "chat_count": 1
        }
    ]
}
```

### 2. Get Chats by Project
**GET** `/api/chats/<project_name>`

Returns all chats filtered by project name.

Example: `GET /api/chats/Lawley`

```json
{
    "success": true,
    "chats": [
        {
            "jid": "120363418298130331@g.us",
            "name": "Lawley Activation 3",
            "last_message_time": "2025-01-26 14:30:15",
            "project_name": "Lawley"
        }
    ]
}
```

### 3. Get Messages for Project Chat
**GET** `/api/messages/<project_name>/<chat_jid>`

Returns messages for a specific chat within a project, with verification that the chat belongs to that project.

Example: `GET /api/messages/Lawley/120363418298130331@g.us?limit=50`

```json
{
    "success": true,
    "messages": [
        {
            "id": "msg123",
            "sender": "27821234567",
            "content": "DR12345 completed",
            "timestamp": "2025-01-26 14:30:15",
            "is_from_me": false,
            "media_type": null,
            "filename": null
        }
    ],
    "project_name": "Lawley",
    "chat_jid": "120363418298130331@g.us"
}
```

## Existing Endpoints (Still Available)

- `GET /api/status` - Check WhatsApp connection status
- `GET /api/contacts` - Get all WhatsApp contacts  
- `GET /api/chats` - Get all chats (all projects)
- `GET /api/messages/<chat_jid>` - Get messages for any chat
- `POST /api/send` - Send WhatsApp message
- `POST /api/assistant` - Process message with LLM

## Frontend Integration Examples

### React Example - Project Selector

```javascript
// Fetch available projects
const fetchProjects = async () => {
    const response = await fetch('/api/projects');
    const data = await response.json();
    if (data.success) {
        setProjects(data.projects);
    }
};

// Fetch chats for selected project
const fetchProjectChats = async (projectName) => {
    const response = await fetch(`/api/chats/${projectName}`);
    const data = await response.json();
    if (data.success) {
        setChats(data.chats);
    }
};

// Fetch messages for project chat
const fetchProjectMessages = async (projectName, chatJid) => {
    const response = await fetch(`/api/messages/${projectName}/${chatJid}?limit=100`);
    const data = await response.json();
    if (data.success) {
        setMessages(data.messages);
    }
};
```

### Frontend Component Structure

```javascript
function ProjectDashboard() {
    const [selectedProject, setSelectedProject] = useState('General');
    const [projects, setProjects] = useState([]);
    const [chats, setChats] = useState([]);
    const [messages, setMessages] = useState([]);
    
    return (
        <div>
            <ProjectSelector 
                projects={projects}
                selected={selectedProject}
                onSelect={setSelectedProject}
            />
            <ChatList 
                chats={chats}
                project={selectedProject}
                onChatSelect={(chatJid) => 
                    fetchProjectMessages(selectedProject, chatJid)
                }
            />
            <MessageView 
                messages={messages}
                project={selectedProject}
            />
        </div>
    );
}
```

## Error Handling

All endpoints return consistent error responses:

```json
{
    "success": false,
    "message": "Error description"
}
```

Common errors:
- `"Database connection failed"` - SQLite database unavailable
- `"Chat not found"` - Invalid chat JID
- `"Chat does not belong to project X"` - JID/project mismatch

## Database Migration Status

✅ **Complete**: 
- Added `project_name` column to `chats` table
- Cleaned database to only track project-specific groups:
  - **Lawley**: 1 chat (Lawley Activation 3 group)
  - **Velo Test**: 1 chat (Velo Test group)
- Updated Go bridge to only store project groups (individual contacts are ignored)
- Created Flask API endpoints for project filtering
- Neon database integration supports both projects with:
  - `installations` table with `project_name` column
  - `qa_photo_reviews` table with `project_name` column
  - Real-time drop monitoring for both groups

## Next Steps for Frontend

1. **Project Selection UI**: Create a dropdown/tabs to switch between projects
2. **Filtered Chat Lists**: Display chats filtered by selected project
3. **Project-Specific Views**: Show drop numbers, statistics per project
4. **Breadcrumb Navigation**: Show current project > chat navigation
5. **Project-Specific Actions**: Send messages within project context

## Test the APIs

You can test the new endpoints using curl:

```bash
# Get all projects
curl http://localhost:5000/api/projects

# Get Lawley project chats
curl http://localhost:5000/api/chats/Lawley

# Get messages from Lawley chat
curl "http://localhost:5000/api/messages/Lawley/120363418298130331@g.us?limit=10"
```