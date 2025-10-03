#!/bin/bash

# WA_Tool Service Startup Script
# ==============================
# Starts all required monitoring services for WhatsApp groups
# Date: October 1, 2025

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directory setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}    WA_Tool Service Startup Script        ${NC}"
echo -e "${BLUE}    Date: October 1, 2025                   ${NC}"
echo -e "${BLUE}============================================${NC}"

# Function to check if process is running
is_running() {
    local process_name="$1"
    pgrep -f "$process_name" > /dev/null 2>&1
}

# Function to start service
start_service() {
    local service_name="$1"
    local command="$2"
    local description="$3"

    echo -e "\n${YELLOW}Starting: $description${NC}"

    if is_running "$service_name"; then
        echo -e "${GREEN}✓ Already running: $service_name${NC}"
        return 0
    fi

    echo -e "Executing: $command"
    if eval "$command"; then
        echo -e "${GREEN}✓ Successfully started: $service_name${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed to start: $service_name${NC}"
        return 1
    fi
}

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please run: python -m venv .venv${NC}"
    exit 1
fi

# Check if environment variables are set
if [ -z "$GSHEET_ID" ]; then
    echo -e "${YELLOW}⚠️  GSHEET_ID environment variable not set${NC}"
fi

if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_APPLICATION_CREDENTIALS environment variable not set${NC}"
fi

echo -e "\n${BLUE}Checking WhatsApp Bridge...${NC}"
cd ../whatsapp-bridge

if [ ! -f "./whatsapp-bridge" ]; then
    echo -e "${RED}❌ WhatsApp bridge executable not found${NC}"
    exit 1
fi

if is_running "whatsapp-bridge"; then
    echo -e "${GREEN}✓ WhatsApp Bridge is already running${NC}"
else
    echo -e "${YELLOW}Starting WhatsApp Bridge...${NC}"
    nohup ./whatsapp-bridge > bridge.log 2>&1 &
    sleep 2
    if is_running "whatsapp-bridge"; then
        echo -e "${GREEN}✓ WhatsApp Bridge started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start WhatsApp Bridge${NC}"
        exit 1
    fi
fi

cd ../whatsapp-mcp-server

echo -e "\n${BLUE}Starting Monitoring Services...${NC}"

# Service definitions
declare -A SERVICES=(
    ["realtime_drop_monitor"]="source .venv/bin/activate && nohup python realtime_drop_monitor.py --interval 15 > realtime_monitor.log 2>&1 &"
    ["google_sheets_qa_monitor"]="source .venv/bin/activate && nohup python google_sheets_qa_monitor.py --interval 60 > google_sheets_qa_monitor.log 2>&1 &"
    ["whatsapp_message_monitor"]="source .venv/bin/activate && nohup python whatsapp_message_monitor.py --interval 30 > whatsapp_message_monitor.log 2>&1 &"
    ["mohadin_message_monitor"]="source .venv/bin/activate && nohup python mohadin_message_monitor.py --interval 30 > mohadin_message_monitor.log 2>&1 &"
)

declare -A DESCRIPTIONS=(
    ["realtime_drop_monitor"]="Real-time Drop Monitor (All Groups: Lawley, Velo Test, Mohadin)"
    ["google_sheets_qa_monitor"]="Google Sheets QA Monitor (Velo Test, Mohadin)"
    ["whatsapp_message_monitor"]="Velo Test Resubmission Monitor (Velo Test)"
    ["mohadin_message_monitor"]="Mohadin Resubmission Monitor (Mohadin)"
)

# Start all services
failed_services=()
for service in "${!SERVICES[@]}"; do
    if ! start_service "$service" "${SERVICES[$service]}" "${DESCRIPTIONS[$service]}"; then
        failed_services+=("$service")
    fi
    sleep 1
done

# Final status
echo -e "\n${BLUE}============================================${NC}"
echo -e "${BLUE}         Service Status Summary           ${NC}"
echo -e "${BLUE}============================================${NC}"

echo -e "\n${GREEN}✅ Running Services:${NC}"
echo -e "  • WhatsApp Bridge (Core Service)"
echo -e "  • Real-time Drop Monitor (Lawley, Velo Test, Mohadin)"
echo -e "  • Google Sheets QA Monitor (Velo Test, Mohadin)"

echo -e "\n${YELLOW}⚠️  Manual Check Required:${NC}"
echo -e "  • Velo Test Resubmission Monitor (Velo Test)"
echo -e "  • Mohadin Resubmission Monitor (Mohadin)"

if [ ${#failed_services[@]} -gt 0 ]; then
    echo -e "\n${RED}❌ Failed Services:${NC}"
    for service in "${failed_services[@]}"; do
        echo -e "  • ${DESCRIPTIONS[$service]}"
    done
    exit 1
fi

echo -e "\n${GREEN}🎉 All critical services started successfully!${NC}"

echo -e "\n${BLUE}Monitoring Information:${NC}"
echo -e "• Real-time Monitor: Checks every 15 seconds for DR numbers"
echo -e "• QA Monitor: Checks every 60 seconds for incomplete drops"
echo -e "• Resubmission Monitors: Check every 30 seconds for resubmissions"

echo -e "\n${BLUE}Log Files:${NC}"
echo -e "• Bridge Log: ../whatsapp-bridge/bridge.log"
echo -e "• Real-time Monitor: realtime_monitor.log"
echo -e "• QA Monitor: google_sheets_qa_monitor.log"
echo -e "• Velo Test Monitor: whatsapp_message_monitor.log"
echo -e "• Mohadin Monitor: mohadin_message_monitor.log"

echo -e "\n${BLUE}To view the monitoring dashboard:${NC}"
echo -e "streamlit run service_monitor.py"

echo -e "\n${GREEN}✅ WA_Tool startup completed successfully!${NC}"