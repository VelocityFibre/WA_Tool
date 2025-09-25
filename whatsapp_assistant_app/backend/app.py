#!/usr/bin/env python3
import os
import json
import requests
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import openai
import logging

# Import custom modules
from templates import get_templates, get_template, add_template, delete_template, fill_template
from scheduler import scheduler

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
WHATSAPP_MCP_URL = os.environ.get('WHATSAPP_MCP_URL', 'http://localhost:3000')
LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
LLM_MODEL = os.environ.get('LLM_MODEL', 'gpt-4')
LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'openai')  # openai, anthropic, etc.

# Create data directory if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data'), exist_ok=True)

# Path to the WhatsApp messages database
MESSAGES_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                              '../whatsapp-mcp/whatsapp-bridge/store/messages.db')

# Initialize LLM client
if LLM_PROVIDER == 'openai' and LLM_API_KEY:
    openai.api_key = LLM_API_KEY

def connect_to_whatsapp_db():
    """Connect to the WhatsApp SQLite database"""
    if not os.path.exists(MESSAGES_DB_PATH):
        logger.error(f"WhatsApp database not found at: {MESSAGES_DB_PATH}")
        return None
    
    try:
        conn = sqlite3.connect(MESSAGES_DB_PATH)
        conn.row_factory = sqlite3.Row  # This enables column access by name
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        return None

def format_phone_number(number):
    """Format phone number with proper country code"""
    if not number.startswith('27'):
        # Remove leading 0 if present and add country code
        if number.startswith('0'):
            number = '27' + number[1:]
        else:
            number = '27' + number
    return number

def get_whatsapp_jid(phone_number):
    """Format phone number as WhatsApp JID"""
    number = format_phone_number(phone_number)
    return f"{number}@s.whatsapp.net"

def call_llm_api(prompt, history=None):
    """Call the LLM API with the given prompt and history"""
    if not history:
        history = []
    
    try:
        if LLM_PROVIDER == 'openai':
            # Format messages for OpenAI
            messages = [{"role": "system", "content": "You are a helpful assistant that helps users communicate via WhatsApp."}]
            
            # Add history
            for entry in history:
                role = "assistant" if entry.get("is_from_me") else "user"
                messages.append({"role": role, "content": entry.get("content", "")})
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=LLM_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
            )
            
            return response.choices[0].message.content
        else:
            # Implement other LLM providers as needed
            return "LLM provider not supported yet."
    except Exception as e:
        logger.error(f"Error calling LLM API: {e}")
        return f"Error: {str(e)}"

def call_whatsapp_api(endpoint, method="GET", data=None):
    """Call the WhatsApp MCP API"""
    url = f"{WHATSAPP_MCP_URL}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            return {"success": False, "message": f"Unsupported method: {method}"}
        
        return response.json()
    except Exception as e:
        logger.error(f"Error calling WhatsApp API: {e}")
        return {"success": False, "message": str(e)}

@app.route('/api/status', methods=['GET'])
def get_status():
    """Check if the WhatsApp MCP server is running"""
    try:
        response = requests.get(f"{WHATSAPP_MCP_URL}/status")
        return jsonify({"whatsapp_connected": response.status_code == 200})
    except:
        return jsonify({"whatsapp_connected": False})

@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    """Get all WhatsApp contacts"""
    response = call_whatsapp_api("contacts")
    return jsonify(response)

@app.route('/api/chats', methods=['GET'])
def get_chats():
    """Get all WhatsApp chats"""
    response = call_whatsapp_api("chats")
    return jsonify(response)

@app.route('/api/messages/<chat_jid>', methods=['GET'])
def get_messages(chat_jid):
    """Get messages for a specific chat"""
    limit = request.args.get('limit', 20)
    response = call_whatsapp_api(f"messages/{chat_jid}?limit={limit}")
    return jsonify(response)

@app.route('/api/send', methods=['POST'])
def send_message():
    """Send a WhatsApp message"""
    data = request.json
    recipient = data.get('recipient')
    message = data.get('message')
    
    if not recipient or not message:
        return jsonify({"success": False, "message": "Recipient and message are required"})
    
    # Format recipient as JID if it's a phone number
    if '@' not in recipient:
        recipient = get_whatsapp_jid(recipient)
    
    response = call_whatsapp_api("send", method="POST", data={
        "recipient": recipient,
        "message": message
    })
    
    return jsonify(response)

@app.route('/api/assistant', methods=['POST'])
def assistant():
    """Process a message with the LLM and send the response via WhatsApp"""
    data = request.json
    recipient = data.get('recipient')
    prompt = data.get('prompt')
    api_key = data.get('api_key')
    
    if not recipient or not prompt:
        return jsonify({"success": False, "message": "Recipient and prompt are required"})
    
    # Use provided API key if available
    current_api_key = LLM_API_KEY
    if api_key:
        if LLM_PROVIDER == 'openai':
            openai.api_key = api_key
    
    # Format recipient as JID if it's a phone number
    if '@' not in recipient:
        recipient = get_whatsapp_jid(recipient)
    
    # Get chat history for context
    conn = connect_to_whatsapp_db()
    if conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, is_from_me, content, type
            FROM messages
            WHERE chat_jid = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (recipient,))
        
        history = [dict(row) for row in cursor.fetchall()]
        history.reverse()  # Oldest first
        conn.close()
    else:
        history = []
    
    # Call LLM API with prompt and history
    llm_response = call_llm_api(prompt, history)
    
    # Restore original API key
    if api_key and LLM_PROVIDER == 'openai':
        openai.api_key = current_api_key
    
    # Send response via WhatsApp
    response = call_whatsapp_api("send", method="POST", data={
        "recipient": recipient,
        "message": llm_response
    })
    
    return jsonify({
        "success": response.get("success", False),
        "message": response.get("message", ""),
        "llm_response": llm_response
    })

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    """Serve the frontend React app"""
    if path and os.path.exists(os.path.join('../frontend/build', path)):
        return send_from_directory('../frontend/build', path)
    else:
        return send_from_directory('../frontend/build', 'index.html')

# Template routes
@app.route('/api/templates', methods=['GET'])
def get_all_templates():
    """Get all message templates"""
    return jsonify({"templates": get_templates()})

@app.route('/api/templates/<template_id>', methods=['GET'])
def get_single_template(template_id):
    """Get a specific template by ID"""
    template = get_template(template_id)
    if template:
        return jsonify({"template": template})
    else:
        return jsonify({"success": False, "message": "Template not found"}), 404

@app.route('/api/templates', methods=['POST'])
def create_template():
    """Create a new template"""
    data = request.json
    name = data.get('name')
    content = data.get('content')
    category = data.get('category', 'General')
    
    if not name or not content:
        return jsonify({"success": False, "message": "Name and content are required"}), 400
    
    success = add_template(name, content, category)
    if success:
        return jsonify({"success": True, "message": "Template created"})
    else:
        return jsonify({"success": False, "message": "Failed to create template"}), 500

@app.route('/api/templates/<template_id>', methods=['DELETE'])
def remove_template(template_id):
    """Delete a template"""
    success = delete_template(template_id)
    if success:
        return jsonify({"success": True, "message": "Template deleted"})
    else:
        return jsonify({"success": False, "message": "Template not found"}), 404

@app.route('/api/templates/<template_id>/fill', methods=['POST'])
def fill_template_route(template_id):
    """Fill a template with variables"""
    data = request.json
    variables = data.get('variables', {})
    
    filled_content = fill_template(template_id, variables)
    if filled_content:
        return jsonify({"success": True, "content": filled_content})
    else:
        return jsonify({"success": False, "message": "Template not found"}), 404

# Scheduler routes
@app.route('/api/schedule', methods=['POST'])
def schedule_message_route():
    """Schedule a message for later sending"""
    data = request.json
    recipient = data.get('recipient')
    message = data.get('message')
    send_time = data.get('send_time')  # ISO format
    metadata = data.get('metadata')
    
    if not recipient or not message or not send_time:
        return jsonify({"success": False, "message": "Recipient, message, and send_time are required"}), 400
    
    # Format recipient as JID if it's a phone number
    if '@' not in recipient:
        recipient = get_whatsapp_jid(recipient)
    
    message_id = scheduler.schedule_message(recipient, message, send_time, metadata)
    if message_id:
        return jsonify({"success": True, "message": "Message scheduled", "id": message_id})
    else:
        return jsonify({"success": False, "message": "Failed to schedule message"}), 500

@app.route('/api/schedule/<message_id>', methods=['DELETE'])
def cancel_scheduled_message(message_id):
    """Cancel a scheduled message"""
    success = scheduler.cancel_message(message_id)
    if success:
        return jsonify({"success": True, "message": "Scheduled message canceled"})
    else:
        return jsonify({"success": False, "message": "Scheduled message not found or already sent"}), 404

@app.route('/api/schedule', methods=['GET'])
def get_scheduled_messages_route():
    """Get all scheduled messages"""
    recipient = request.args.get('recipient')
    messages = scheduler.get_scheduled_messages(recipient)
    return jsonify({"scheduled_messages": messages})

@app.route('/api/schedule/history', methods=['GET'])
def get_message_history_route():
    """Get history of sent scheduled messages"""
    limit = request.args.get('limit', 100, type=int)
    history = scheduler.get_message_history(limit)
    return jsonify({"message_history": history})

# Start the scheduler when the app starts
scheduler.ensure_scheduler_running()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
