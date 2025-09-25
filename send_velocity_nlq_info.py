#!/usr/bin/env python3
"""
Script to send information about Velocity Fibre NLQ System via WhatsApp
"""
import requests
import json
import sys

# WhatsApp Bridge API endpoint
API_URL = "http://localhost:8080/api/send"

# Recipient phone number (continuing with the same US number)
RECIPIENT = "12145432065@s.whatsapp.net"

# Message content with WhatsApp-friendly formatting
MESSAGE = """*Busy building this for a Fibre Company: Velocity Fibre NLQ System: Enhanced with Business Insights*

*What We've Done*
Added business insights capabilities to your NLQ system, enabling analytical questions beyond basic data retrieval.

*Real Examples (Just Tested)*
Question 1: "What business insights can we derive from our project data?"
Answer: "Based on the information available, we can derive valuable business insights from project data such as customer acquisition trends, project completion rates, resource allocation efficiency, and customer satisfaction levels."

Question 2: "What trends can you identify in our customer data?"
Answer: "Based on the available database results, we can identify a trend of increasing customer subscriptions to higher-speed fiber optic plans over the past year."

*Business Impact*
• Management can now ask broad analytical questions without SQL knowledge
• Immediate business intelligence without waiting for reports
• Competitive advantage through advanced AI capabilities

*Status & Next Steps*
• Ready now: System deployed with vector store ID configured
• Next: Enrich vector store with more business documents, create data embeddings, integrate with Zep/Qdrant, implement visualizations

This enhancement transforms your system from a data query tool into a comprehensive business intelligence platform for Velocity Fibre."""

def send_message():
    """Send message to recipient via WhatsApp Bridge API"""
    payload = {
        "recipient": RECIPIENT,
        "message": MESSAGE
    }
    
    try:
        response = requests.post(API_URL, json=payload)
        response_data = response.json()
        
        if response.status_code == 200 and response_data.get("success"):
            print(f"Message sent successfully to {RECIPIENT}")
            return True
        else:
            print(f"Failed to send message: {response_data.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return False

if __name__ == "__main__":
    print(f"Sending Velocity Fibre NLQ System information to {RECIPIENT}...")
    send_message()
