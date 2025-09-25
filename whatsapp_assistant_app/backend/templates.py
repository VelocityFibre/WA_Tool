#!/usr/bin/env python3
"""
Message template management for WhatsApp Assistant
"""
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Path to templates file
TEMPLATES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/templates.json')

# Default templates
DEFAULT_TEMPLATES = [
    {
        "id": "greeting",
        "name": "Greeting",
        "content": "Hello {name}, how are you today?",
        "category": "General"
    },
    {
        "id": "meeting_reminder",
        "name": "Meeting Reminder",
        "content": "Hi {name}, just a reminder about our meeting {time}. Please let me know if you can make it.",
        "category": "Business"
    },
    {
        "id": "thank_you",
        "name": "Thank You",
        "content": "Thank you for your {item}, {name}! I really appreciate it.",
        "category": "General"
    },
    {
        "id": "follow_up",
        "name": "Follow Up",
        "content": "Hi {name}, I'm following up on our conversation about {topic}. Any updates?",
        "category": "Business"
    }
]

def ensure_templates_file():
    """Ensure the templates file exists, create it if it doesn't"""
    os.makedirs(os.path.dirname(TEMPLATES_FILE), exist_ok=True)
    
    if not os.path.exists(TEMPLATES_FILE):
        with open(TEMPLATES_FILE, 'w') as f:
            json.dump(DEFAULT_TEMPLATES, f, indent=2)
        logger.info(f"Created default templates file at {TEMPLATES_FILE}")

def get_templates():
    """Get all message templates"""
    ensure_templates_file()
    
    try:
        with open(TEMPLATES_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading templates: {e}")
        return DEFAULT_TEMPLATES

def get_template(template_id):
    """Get a specific template by ID"""
    templates = get_templates()
    for template in templates:
        if template['id'] == template_id:
            return template
    return None

def add_template(name, content, category="General"):
    """Add a new template"""
    templates = get_templates()
    
    # Generate a unique ID
    template_id = name.lower().replace(' ', '_')
    
    # Check if template with this ID already exists
    for i, template in enumerate(templates):
        if template['id'] == template_id:
            # Update existing template
            templates[i] = {
                "id": template_id,
                "name": name,
                "content": content,
                "category": category
            }
            break
    else:
        # Add new template
        templates.append({
            "id": template_id,
            "name": name,
            "content": content,
            "category": category
        })
    
    # Save templates
    try:
        with open(TEMPLATES_FILE, 'w') as f:
            json.dump(templates, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving template: {e}")
        return False

def delete_template(template_id):
    """Delete a template by ID"""
    templates = get_templates()
    
    # Filter out the template to delete
    new_templates = [t for t in templates if t['id'] != template_id]
    
    if len(new_templates) == len(templates):
        # No template was removed
        return False
    
    # Save templates
    try:
        with open(TEMPLATES_FILE, 'w') as f:
            json.dump(new_templates, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error deleting template: {e}")
        return False

def fill_template(template_id, variables):
    """Fill a template with variables"""
    template = get_template(template_id)
    if not template:
        return None
    
    try:
        content = template['content']
        for key, value in variables.items():
            content = content.replace(f"{{{key}}}", value)
        return content
    except Exception as e:
        logger.error(f"Error filling template: {e}")
        return template['content']
