#!/bin/bash

# Google Sheets QA Monitor Management Script
# ==========================================

SERVICE_NAME="google-sheets-qa-monitor"
SCRIPT_PATH="/home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server/google_sheets_qa_monitor.py"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
LOG_FILE="/home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server/google_sheets_qa_monitor.log"

show_usage() {
    echo "Google Sheets QA Monitor Management"
    echo "Usage: $0 {start|stop|restart|status|logs|install|test|dry-run}"
    echo ""
    echo "Commands:"
    echo "  start    - Start the Google Sheets QA monitor"
    echo "  stop     - Stop the monitor"
    echo "  restart  - Restart the monitor"
    echo "  status   - Show service status"
    echo "  logs     - Show live logs"
    echo "  install  - Install as systemd service"
    echo "  test     - Run single test check"
    echo "  dry-run  - Run in dry-run mode (foreground)"
}

install_service() {
    echo "Installing Google Sheets QA Monitor as systemd service..."
    
    # Create the service file
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=Google Sheets QA Monitor - Watches for Incomplete flags
After=network.target
Wants=network.target

[Service]
Type=simple
User=louisdup
Group=louisdup
WorkingDirectory=/home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server
ExecStart=/home/louisdup/.local/bin/uv run python google_sheets_qa_monitor.py --interval 60
Restart=always
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=google-sheets-qa-monitor

# Environment
Environment=PYTHONUNBUFFERED=1
Environment=GSHEET_ID=1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk
Environment=GOOGLE_APPLICATION_CREDENTIALS=/home/louisdup/VF/Apps/google_sheets/sheets-credentials.json

# Security
NoNewPrivileges=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable $SERVICE_NAME
    
    echo "✅ Service installed successfully!"
    echo "Use: sudo systemctl start $SERVICE_NAME"
}

start_service() {
    echo "Starting Google Sheets QA Monitor..."
    sudo systemctl start $SERVICE_NAME
    sleep 2
    sudo systemctl status $SERVICE_NAME --no-pager -l
}

stop_service() {
    echo "Stopping Google Sheets QA Monitor..."
    sudo systemctl stop $SERVICE_NAME
    echo "✅ Service stopped"
}

restart_service() {
    echo "Restarting Google Sheets QA Monitor..."
    sudo systemctl restart $SERVICE_NAME
    sleep 2
    sudo systemctl status $SERVICE_NAME --no-pager -l
}

show_status() {
    echo "Google Sheets QA Monitor Status:"
    echo "==============================="
    sudo systemctl status $SERVICE_NAME --no-pager -l
    echo ""
    echo "Recent logs:"
    echo "============"
    sudo journalctl -u $SERVICE_NAME --no-pager -n 10
}

show_logs() {
    echo "Following Google Sheets QA Monitor logs (Ctrl+C to exit):"
    echo "========================================================="
    sudo journalctl -u $SERVICE_NAME -f
}

run_test() {
    echo "Running Google Sheets QA Monitor test..."
    echo "========================================"
    export GSHEET_ID="1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk"
    export GOOGLE_APPLICATION_CREDENTIALS="/home/louisdup/VF/Apps/google_sheets/sheets-credentials.json"
    
    cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server
    uv run python google_sheets_qa_monitor.py --test
}

run_dry_run() {
    echo "Running Google Sheets QA Monitor in dry-run mode..."
    echo "==================================================="
    export GSHEET_ID="1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk"
    export GOOGLE_APPLICATION_CREDENTIALS="/home/louisdup/VF/Apps/google_sheets/sheets-credentials.json"
    
    cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server
    uv run python google_sheets_qa_monitor.py --dry-run --interval 30
}

# Main command handling
case "$1" in
    start)
        start_service
        ;;
    stop)
        stop_service
        ;;
    restart)
        restart_service
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    install)
        install_service
        ;;
    test)
        run_test
        ;;
    dry-run)
        run_dry_run
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

exit 0