#!/bin/bash

# Setup Google Sheets Environment Variables for Velo Test Dual-Write
# ==================================================================

echo "🔧 Setting up Google Sheets environment for Velo Test dual-write..."

# Set credentials path
CREDENTIALS_PATH="/home/louisdup/VF/Apps/google_sheets/sheets-api-473708-ceecae31f013 (1).json"

echo "📋 Please provide your Google Sheet ID:"
echo "   (This is the long ID from your Google Sheets URL)"
echo "   Example: https://docs.google.com/spreadsheets/d/[THIS_IS_THE_SHEET_ID]/edit"
echo ""
read -p "🆔 Enter your GSHEET_ID: " GSHEET_ID

if [ -z "$GSHEET_ID" ]; then
    echo "❌ Sheet ID cannot be empty!"
    exit 1
fi

# Verify credentials file exists
if [ ! -f "$CREDENTIALS_PATH" ]; then
    echo "❌ Credentials file not found: $CREDENTIALS_PATH"
    exit 1
fi

echo "✅ Credentials file found: $CREDENTIALS_PATH"

# Export environment variables
export GSHEET_ID="$GSHEET_ID"
export GOOGLE_APPLICATION_CREDENTIALS="$CREDENTIALS_PATH"

echo ""
echo "🎯 Environment variables set:"
echo "   GSHEET_ID=$GSHEET_ID"
echo "   GOOGLE_APPLICATION_CREDENTIALS=$CREDENTIALS_PATH"

# Test the connection
echo ""
echo "🧪 Testing Google Sheets connection..."
cd /home/louisdup/VF/Apps/google_sheets
python test_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Google Sheets connection successful!"
    echo ""
    echo "📝 To make these environment variables permanent, add to your ~/.bashrc:"
    echo "export GSHEET_ID=\"$GSHEET_ID\""
    echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$CREDENTIALS_PATH\""
    echo ""
    echo "🚀 Now you can restart the realtime monitor to enable dual-write:"
    echo "cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server"
    echo "./manage_monitor.sh restart"
else
    echo ""
    echo "❌ Google Sheets connection failed!"
    echo "Please check your Sheet ID and credentials file."
fi