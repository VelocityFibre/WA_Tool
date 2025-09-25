# How to Run and Use WhatsApp MCP

This guide provides step-by-step instructions on how to set up, run, and use the WhatsApp MCP (Machine Conversation Protocol) server to interact with WhatsApp through AI assistants.

## Overview

The WhatsApp MCP consists of two main components:

1. **Go WhatsApp Bridge**: Connects to WhatsApp's web API and provides a REST API interface
2. **Python MCP Server**: Implements the Model Context Protocol for AI assistants to interact with WhatsApp

## Setup Instructions

### Prerequisites

- Go installed
- Python 3.6+ installed
- UV (Python package manager) installed
- WhatsApp account on your phone

### Step 1: Run the WhatsApp Bridge

The WhatsApp bridge is the component that connects to WhatsApp's web API and provides a REST API for the MCP server to interact with.

```bash
cd /home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/whatsapp-mcp/whatsapp-bridge
go run main.go
```

When you run this command for the first time, you'll see a QR code in the terminal. Scan this QR code with your WhatsApp mobile app to authenticate:

1. Open WhatsApp on your phone
2. Go to Settings > Linked Devices
3. Tap on "Link a Device"
4. Scan the QR code displayed in your terminal

After successful authentication, you should see output similar to:

```
[Client INFO] Starting WhatsApp client...
[Client INFO] Successfully authenticated
[Client INFO] Connected to WhatsApp

✓ Connected to WhatsApp! Type 'help' for commands.
Starting REST API server on :8080...
REST server is running. Press Ctrl+C to disconnect and exit.
```

This confirms that:
- The bridge has successfully connected to WhatsApp
- It's authenticated and ready to use
- The REST API server is running on port 8080
- It may show some of your existing chats

The bridge will remain running in the background until you stop it with Ctrl+C.

### Step 2: Configure the MCP Server

The MCP configuration needs to be set up to allow AI assistants to interact with WhatsApp. The configuration has been added to:

```
/home/ldp/.codeium/windsurf/mcp_config.json
```

With the following configuration:

```json
"whatsapp": {
  "command": "/home/ldp/.local/bin/uv",
  "args": [
    "--directory",
    "/home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/whatsapp-mcp/whatsapp-mcp-server",
    "run",
    "main.py"
  ]
}
```

## Using WhatsApp MCP

Once both the WhatsApp bridge and MCP server are running, you can use the following MCP tools to interact with WhatsApp:

### Sending Messages

To send a message to a contact:

```
mcp4_send_message(recipient="PHONE_NUMBER", message="YOUR_MESSAGE")
```

Example:
```
mcp4_send_message(recipient="27824939462", message="Hello, how are you?")
```

Successful response:
```json
{
  "success": true,
  "message": "Message sent to 27824939462"
}
```

### Other Available Tools

- **mcp4_search_contacts**: Search for contacts by name or phone number
- **mcp4_list_messages**: Retrieve messages with optional filters and context
- **mcp4_list_chats**: List available chats with metadata
- **mcp4_get_chat**: Get information about a specific chat
- **mcp4_get_direct_chat_by_contact**: Find a direct chat with a specific contact
- **mcp4_get_contact_chats**: List all chats involving a specific contact
- **mcp4_get_last_interaction**: Get the most recent message with a contact
- **mcp4_get_message_context**: Retrieve context around a specific message
- **mcp4_send_file**: Send a file (image, video, raw audio, document) to a specified recipient
- **mcp4_send_audio_message**: Send an audio file as a WhatsApp voice message
- **mcp4_download_media**: Download media from a WhatsApp message and get the local file path
## Detailed Usage Examples

### Sending Messages

The most basic operation is sending a text message:

```
mcp4_send_message(recipient="27824939462", message="Hello, how are you?")
```

When sending messages, you can use either:
- A phone number with country code (no + symbol): `"27824939462"`
- A full JID for groups: `"123456789@g.us"`

### Listing and Searching Chats

To list your recent WhatsApp chats:

```python
mcp4_list_chats(limit=10, include_last_message=True)
```

To search for a specific chat by name:

```python
mcp4_list_chats(query="John", limit=5)
```

### Reading Messages

To retrieve recent messages from a specific chat:

```python
mcp4_list_messages(chat_jid="27824939462@s.whatsapp.net", limit=10)
```

To search for messages containing specific text:

```python
mcp4_list_messages(query="meeting", limit=20)
```

To get context around a specific message:

```python
mcp4_get_message_context(message_id="MESSAGE_ID", before=5, after=5)
```

### Working with Contacts

To search for a contact:

```python
mcp4_search_contacts(query="John")
```

To get all chats involving a specific contact:

```python
mcp4_get_contact_chats(jid="27824939462@s.whatsapp.net")
```

To get the most recent interaction with a contact:

```python
mcp4_get_last_interaction(jid="27824939462@s.whatsapp.net")
```

### Sending Media

To send an image, video, or document:

```python
mcp4_send_file(recipient="27824939462", media_path="/path/to/file.jpg")
```

To send a voice message (requires .ogg file in Opus format or ffmpeg installed):

```python
mcp4_send_audio_message(recipient="27824939462", media_path="/path/to/audio.ogg")
```

### Downloading Media

To download media from a message:

```python
mcp4_download_media(message_id="MESSAGE_ID", chat_jid="CHAT_JID")
```

## Advanced Usage

### Automating WhatsApp Bridge Startup

You can create a startup script to automatically launch the WhatsApp bridge:

```bash
#!/bin/bash
cd /home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/whatsapp-mcp/whatsapp-bridge
nohup go run main.go > whatsapp_bridge.log 2>&1 &
echo "WhatsApp bridge started with PID $!"
```

Save this as `start_whatsapp_bridge.sh` and make it executable with `chmod +x start_whatsapp_bridge.sh`.

### Monitoring WhatsApp Bridge Status

To check if the WhatsApp bridge is running:

```bash
ps aux | grep "whatsapp-bridge" | grep -v grep
```

To check the logs if you've started it with the script above:

```bash
tail -f /home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/whatsapp-mcp/whatsapp-bridge/whatsapp_bridge.log
```

### Direct API Interaction

If needed, you can interact directly with the WhatsApp bridge API using curl:

```bash
# Send a message
curl -X POST http://localhost:8080/api/send -H "Content-Type: application/json" -d '{"recipient":"27824939462", "message":"Hello from curl!"}'

# Download media
curl -X POST http://localhost:8080/api/download -H "Content-Type: application/json" -d '{"message_id":"MESSAGE_ID", "chat_jid":"CHAT_JID"}'
```

## Troubleshooting

### WhatsApp Bridge Not Connecting

If the WhatsApp bridge fails to connect:

1. Check if the bridge is already running in another terminal
2. Ensure your internet connection is stable
3. Try restarting the bridge
4. If you see "address already in use" error, it means the bridge is already running


### Authentication Issues

If you encounter authentication issues:

1. Make sure you've scanned the QR code correctly
2. Check if your WhatsApp account has reached the device limit (up to 4 devices)
3. Try deleting the database files and re-authenticating:

   ```bash
   rm /home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/whatsapp-mcp/whatsapp-bridge/store/messages.db
   rm /home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/whatsapp-mcp/whatsapp-bridge/store/whatsapp.db
   ```

### MCP Tools Not Working

If the MCP tools are not working:

1. Ensure both the WhatsApp bridge and MCP server are running
2. Check if the MCP configuration in `mcp_config.json` is correct
3. Restart the AI assistant to reload the MCP configuration


### Common Error Messages

#### "Not connected to WhatsApp"

This means the WhatsApp bridge is running but not connected to WhatsApp. Try restarting the bridge.

#### "Error parsing JID"

This indicates an invalid phone number or JID format. Make sure you're using the correct format.

#### "Request error: Post `http://localhost:8080/api/send`"

This suggests the WhatsApp bridge is not running. Start the bridge and try again.

## Security Considerations

The WhatsApp bridge stores your WhatsApp session data locally in SQLite databases. Messages are stored locally and only sent to AI assistants when explicitly requested. Be cautious about sharing sensitive information through WhatsApp when using this integration. Consider the privacy implications of allowing AI assistants to access your WhatsApp messages. The connection to WhatsApp is secured using WhatsApp's own encryption protocols.
- The WhatsApp bridge stores your WhatsApp session data locally in SQLite databases
- Messages are stored locally and only sent to AI assistants when explicitly requested
- Be cautious about sharing sensitive information through WhatsApp when using this integration
- Consider the privacy implications of allowing AI assistants to access your WhatsApp messages
- The connection to WhatsApp is secured using WhatsApp's own encryption protocols
