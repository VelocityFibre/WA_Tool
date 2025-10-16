#!/usr/bin/env python3
"""
Create Mohadin WA_Tool Monitor Tab
==================================

This script safely creates a duplicate of the Mohadin tab for WA_Tool monitoring
without interfering with the production data.
"""

import os
import sys
import json

# Add the server directory to path for imports
sys.path.insert(0, 'whatsapp-mcp/whatsapp-mcp-server')

try:
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    print("✅ Google Sheets libraries loaded successfully")
except ImportError as e:
    print(f"❌ Google Sheets libraries not available: {e}")
    print("Install with: uv add google-api-python-client google-auth")
    sys.exit(1)

# Configuration
SPREADSHEET_ID = "1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk"
PRODUCTION_TAB_NAME = "Mohadin"
PRODUCTION_TAB_GID = 1459373573
MONITOR_TAB_NAME = "Mohadin WA_Tool Monitor"
CREDENTIALS_PATH = "./credentials.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_sheets_service():
    """Get Google Sheets service connection"""
    try:
        if not os.path.exists(CREDENTIALS_PATH):
            print(f"❌ Credentials file not found: {CREDENTIALS_PATH}")
            return None
            
        credentials = Credentials.from_service_account_file(
            CREDENTIALS_PATH, scopes=SCOPES
        )
        return build("sheets", "v4", credentials=credentials, cache_discovery=False)
    except Exception as e:
        print(f"❌ Failed to create Google Sheets service: {e}")
        return None

def duplicate_sheet(service):
    """Duplicate the Mohadin tab"""
    try:
        print(f"📋 Duplicating '{PRODUCTION_TAB_NAME}' tab...")
        
        # Duplicate the sheet
        request = {
            "duplicateSheet": {
                "sourceSheetId": PRODUCTION_TAB_GID,
                "insertSheetIndex": 0,  # Insert at beginning
                "newSheetName": MONITOR_TAB_NAME
            }
        }
        
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"requests": [request]}
        ).execute()
        
        # Extract the new sheet ID
        new_sheet_id = response['replies'][0]['duplicateSheet']['properties']['sheetId']
        print(f"✅ Successfully duplicated tab with ID: {new_sheet_id}")
        return new_sheet_id
        
    except HttpError as e:
        if "already exists" in str(e):
            print(f"⚠️  Tab '{MONITOR_TAB_NAME}' already exists")
            # Get existing sheet ID
            spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == MONITOR_TAB_NAME:
                    return sheet['properties']['sheetId']
        else:
            print(f"❌ Error duplicating sheet: {e}")
            return None
    except Exception as e:
        print(f"❌ Error duplicating sheet: {e}")
        return None

def clear_data_rows(service, sheet_id):
    """Clear all data rows but keep headers"""
    try:
        print(f"🧹 Clearing data rows from '{MONITOR_TAB_NAME}' (keeping headers)...")
        
        # First, get the sheet data to determine the range
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{MONITOR_TAB_NAME}'!A:Z"
        ).execute()
        
        values = result.get('values', [])
        if len(values) <= 1:
            print("✅ No data rows to clear (only headers present)")
            return True
            
        # Clear everything except the header row
        num_rows = len(values)
        if num_rows > 1:
            clear_range = f"'{MONITOR_TAB_NAME}'!A2:Z{num_rows}"
            service.spreadsheets().values().clear(
                spreadsheetId=SPREADSHEET_ID,
                range=clear_range
            ).execute()
            print(f"✅ Cleared {num_rows-1} data rows (kept headers)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error clearing data rows: {e}")
        return False

def update_config_file(sheet_id):
    """Update the configuration file with the new sheet ID"""
    try:
        config_path = "projects/mohadin/config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        config['google_sheets']['test_tab_gid'] = str(sheet_id)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
            
        print(f"✅ Updated config.json with monitor tab GID: {sheet_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating config file: {e}")
        return False

def main():
    """Main execution"""
    print("🚀 Starting Mohadin WA_Tool Monitor tab creation...")
    print()
    
    # Get Google Sheets service
    service = get_sheets_service()
    if not service:
        return False
    
    # Duplicate the production tab
    new_sheet_id = duplicate_sheet(service)
    if not new_sheet_id:
        return False
    
    # Clear data rows (keep headers)
    if not clear_data_rows(service, new_sheet_id):
        return False
    
    # Update configuration
    if not update_config_file(new_sheet_id):
        return False
    
    print()
    print("🎉 SUCCESS! Monitor tab created successfully!")
    print("=" * 50)
    print(f"✅ Tab name: '{MONITOR_TAB_NAME}'")
    print(f"✅ Tab GID: {new_sheet_id}")
    print(f"✅ Status: Ready for automation")
    print(f"✅ Production tab: Completely safe and untouched")
    print()
    print("🔧 Configuration updated - ready to restart monitoring!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)