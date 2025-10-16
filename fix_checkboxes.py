#!/usr/bin/env python3
"""
Fix Checkboxes in Mohadin WA_Tool Monitor Tab
=============================================

This script adds proper checkbox formatting to columns V, W, X in the monitor tab.
"""

import os
import sys

# Add the server directory to path for imports
sys.path.insert(0, 'whatsapp-mcp/whatsapp-mcp-server')

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    print("✅ Google Sheets libraries loaded successfully")
except ImportError as e:
    print(f"❌ Google Sheets libraries not available: {e}")
    sys.exit(1)

# Configuration
SPREADSHEET_ID = "1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk"
MONITOR_TAB_NAME = "Mohadin WA_Tool Monitor"
MONITOR_TAB_GID = 1306359696
CREDENTIALS_PATH = "./credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheets_service():
    """Get Google Sheets service connection"""
    try:
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=SCOPES
        )
        return build("sheets", "v4", credentials=credentials, cache_discovery=False)
    except Exception as e:
        print(f"❌ Failed to create Google Sheets service: {e}")
        return None

def add_checkboxes(service):
    """Add checkbox data validation to columns V, W, X"""
    try:
        print(f"☑️  Adding checkboxes to columns V, W, X in '{MONITOR_TAB_NAME}'...")
        
        # Define the checkbox validation
        checkbox_validation = {
            "condition": {
                "type": "BOOLEAN"
            },
            "inputMessage": "Click to toggle checkbox",
            "strict": True
        }
        
        # Requests to add checkboxes to columns V (21), W (22), X (23)
        # Using a large range to cover all possible rows
        requests = []
        
        # Column V (index 21) - Incomplete
        requests.append({
            "setDataValidation": {
                "range": {
                    "sheetId": MONITOR_TAB_GID,
                    "startRowIndex": 0,  # Start from header row
                    "endRowIndex": 5000,  # Large range to cover all rows
                    "startColumnIndex": 21,  # Column V
                    "endColumnIndex": 22
                },
                "rule": checkbox_validation
            }
        })
        
        # Column W (index 22) - Resubmitted  
        requests.append({
            "setDataValidation": {
                "range": {
                    "sheetId": MONITOR_TAB_GID,
                    "startRowIndex": 0,
                    "endRowIndex": 5000,
                    "startColumnIndex": 22,  # Column W
                    "endColumnIndex": 23
                },
                "rule": checkbox_validation
            }
        })
        
        # Column X (index 23) - Completed
        requests.append({
            "setDataValidation": {
                "range": {
                    "sheetId": MONITOR_TAB_GID,
                    "startRowIndex": 0,
                    "endRowIndex": 5000,
                    "startColumnIndex": 23,  # Column X
                    "endColumnIndex": 24
                },
                "rule": checkbox_validation
            }
        })
        
        # Execute the batch update
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": requests}
        ).execute()
        
        print("✅ Successfully added checkboxes to columns V, W, X")
        return True
        
    except Exception as e:
        print(f"❌ Error adding checkboxes: {e}")
        return False

def set_default_values(service):
    """Set default FALSE values for checkboxes"""
    try:
        print("📋 Setting default FALSE values for checkboxes...")
        
        # Set default values in the header row if needed
        values = [
            ['FALSE'],  # Column V
            ['FALSE'],  # Column W  
            ['FALSE']   # Column X
        ]
        
        # Update columns V, W, X in row 2 (first data row) as examples
        ranges = [
            f"'{MONITOR_TAB_NAME}'!V2",
            f"'{MONITOR_TAB_NAME}'!W2", 
            f"'{MONITOR_TAB_NAME}'!X2"
        ]
        
        for i, range_name in enumerate(ranges):
            service.spreadsheets().values().update(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name,
                valueInputOption='RAW',
                body={'values': [values[i]]}
            ).execute()
        
        print("✅ Default checkbox values set")
        return True
        
    except Exception as e:
        print(f"❌ Error setting default values: {e}")
        return False

def main():
    """Main execution"""
    print("🔧 Starting checkbox formatting for Mohadin WA_Tool Monitor...")
    print()
    
    # Get Google Sheets service
    service = get_sheets_service()
    if not service:
        return False
    
    # Add checkboxes to columns V, W, X
    if not add_checkboxes(service):
        return False
    
    # Set default values
    if not set_default_values(service):
        return False
    
    print()
    print("🎉 SUCCESS! Checkboxes added successfully!")
    print("=" * 50)
    print("✅ Column V (Incomplete): Checkbox formatting applied")
    print("✅ Column W (Resubmitted): Checkbox formatting applied") 
    print("✅ Column X (Completed): Checkbox formatting applied")
    print()
    print("📊 Check the sheet - you should now see proper checkboxes!")
    print("https://docs.google.com/spreadsheets/d/1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk/")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)