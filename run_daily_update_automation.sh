#!/bin/bash

# Script to automate the daily WhatsApp extraction and Airtable processing
# Created on 2025-05-23

# Set up logging
LOG_DIR="/home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor/logs"
LOG_FILE="$LOG_DIR/automation_$(date +%Y-%m-%d).log"
mkdir -p "$LOG_DIR"

# Function to log messages
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Set paths
WHATSAPP_DIR="/home/ldp/louisdup/Clients/VelocityFibre/Agents/WhatsAppMonitor"
AIRTABLE_DIR="/home/ldp/louisdup/Clients/VelocityFibre/Agents/Airtable"

# Get yesterday's date (for catching up on missed days)
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)

# Log start of automation
log "Starting daily update automation"

# Check if WhatsApp bridge is running
if ! pgrep -f "whatsapp-bridge" > /dev/null; then
    log "WARNING: WhatsApp bridge is not running."
    
    # Check if this is a test run
    if [[ "$1" == "--test" ]]; then
        log "Test mode: Continuing without WhatsApp bridge..."
    else
        log "Attempting to start WhatsApp bridge..."
        cd "$WHATSAPP_DIR/whatsapp-mcp/whatsapp-bridge" || exit 1
        nohup go run main.go > whatsapp_bridge.log 2>&1 &
        sleep 10  # Give it time to start
        
        if ! pgrep -f "whatsapp-bridge" > /dev/null; then
            log "ERROR: Failed to start WhatsApp bridge."
            log "Please start the WhatsApp bridge manually and scan the QR code."
            log "Then run this script again."
            exit 1
        else
            log "WhatsApp bridge started successfully."
        fi
    fi
fi

# Run extraction for yesterday (to catch any missed updates)
log "Running extraction for yesterday ($YESTERDAY)"
cd "$WHATSAPP_DIR" || exit 1
python3 extract_daily_update.py --date "$YESTERDAY"

# Run extraction for today
TODAY=$(date +%Y-%m-%d)
log "Running extraction for today ($TODAY)"
python3 extract_daily_update.py --date "$TODAY"

# Process WhatsApp updates in Airtable
log "Processing WhatsApp updates in Airtable"
cd "$AIRTABLE_DIR" || exit 1
python3 process_whatsapp_updates.py

# Log completion
log "Daily update automation completed"

exit 0
