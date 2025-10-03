#!/bin/bash
#
# WhatsApp Drop Monitor Management Script
# Usage: ./manage_monitor.sh [start|stop|restart|status|logs|install|test]
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="whatsapp-drop-monitor.service"
SERVICE_NAME="whatsapp-drop-monitor"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        log_error "uv package manager not found. Please install uv first."
        exit 1
    fi
    
    # Check if WhatsApp bridge database exists
    if [ ! -f "../whatsapp-bridge/store/messages.db" ]; then
        log_warning "WhatsApp database not found. Make sure the WhatsApp bridge is running."
    fi
    
    log_success "Prerequisites OK"
}

install_service() {
    log_info "Installing systemd service..."
    
    check_prerequisites
    
    # Copy service file to systemd directory
    sudo cp "$SCRIPT_DIR/$SERVICE_FILE" "/etc/systemd/system/"
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service (auto-start on boot)
    sudo systemctl enable "$SERVICE_NAME"
    
    log_success "Service installed and enabled for auto-start"
}

start_service() {
    log_info "Starting WhatsApp drop monitor..."
    sudo systemctl start "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Monitor started successfully"
        show_status
    else
        log_error "Failed to start monitor"
        sudo systemctl status "$SERVICE_NAME" --no-pager
        exit 1
    fi
}

stop_service() {
    log_info "Stopping WhatsApp drop monitor..."
    sudo systemctl stop "$SERVICE_NAME"
    
    if ! systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Monitor stopped successfully"
    else
        log_error "Failed to stop monitor"
        exit 1
    fi
}

restart_service() {
    log_info "Restarting WhatsApp drop monitor..."
    sudo systemctl restart "$SERVICE_NAME"
    
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        log_success "Monitor restarted successfully"
        show_status
    else
        log_error "Failed to restart monitor"
        sudo systemctl status "$SERVICE_NAME" --no-pager
        exit 1
    fi
}

show_status() {
    log_info "Monitor status:"
    sudo systemctl status "$SERVICE_NAME" --no-pager --lines=10
}

show_logs() {
    log_info "Recent logs:"
    sudo journalctl -u "$SERVICE_NAME" --no-pager -f
}

test_monitor() {
    log_info "Testing monitor in dry-run mode..."
    cd "$SCRIPT_DIR"
    uv run python realtime_drop_monitor.py --interval 5 --dry-run &
    MONITOR_PID=$!
    
    log_info "Monitor started with PID $MONITOR_PID. Press Ctrl+C to stop test."
    
    # Wait for user to stop
    wait $MONITOR_PID
    log_success "Test completed"
}

# Main script logic
case "$1" in
    install)
        install_service
        ;;
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
    test)
        test_monitor
        ;;
    *)
        echo "Usage: $0 {install|start|stop|restart|status|logs|test}"
        echo ""
        echo "Commands:"
        echo "  install  - Install the monitor as a systemd service"
        echo "  start    - Start the monitor service"
        echo "  stop     - Stop the monitor service"
        echo "  restart  - Restart the monitor service"
        echo "  status   - Show service status"
        echo "  logs     - Show and follow service logs"
        echo "  test     - Test the monitor in dry-run mode"
        echo ""
        exit 1
        ;;
esac

exit 0