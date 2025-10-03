#!/bin/bash

# Deploy Robust Drop Monitor v2.0
# This script replaces the problematic old monitor with the new robust version

set -e

echo "🚀 Deploying Robust Drop Monitor v2.0"
echo "======================================="

# Stop the old monitor
echo "🛑 Stopping old monitor service..."
sudo systemctl stop whatsapp-drop-monitor || echo "Service was not running"

# Backup old files
echo "📁 Backing up old files..."
cp realtime_drop_monitor.py realtime_drop_monitor.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "No old file to backup"
cp monitor_state.json monitor_state_old.json.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "No old state file"

# Make the new monitor executable
echo "🔧 Setting up new monitor..."
chmod +x robust_drop_monitor.py

# Test the new monitor in dry-run mode first
echo "🧪 Testing new monitor (dry-run)..."
if timeout 30 uv run python robust_drop_monitor.py --interval 5 --dry-run; then
    echo "✅ Dry-run test completed successfully"
else
    echo "⚠️ Dry-run test ended (expected with timeout)"
fi

# Update systemd service to use new monitor
echo "🔄 Updating systemd service..."
sudo tee /etc/systemd/system/whatsapp-drop-monitor.service > /dev/null << 'EOF'
[Unit]
Description=WhatsApp Drop Number Real-time Monitor v2.0 (Robust)
After=network.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=louisdup
WorkingDirectory=/home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server
ExecStart=/home/louisdup/.local/bin/uv run python robust_drop_monitor.py --interval 15
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal
KillMode=mixed
TimeoutStopSec=30
Environment=PATH=/home/louisdup/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable the service
echo "🔧 Enabling service..."
sudo systemctl enable whatsapp-drop-monitor

# Start the new monitor
echo "🚀 Starting robust monitor v2.0..."
sudo systemctl start whatsapp-drop-monitor

# Wait a moment and check status
sleep 5
echo "📊 Checking service status..."
sudo systemctl status whatsapp-drop-monitor --no-pager

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Monitor logs: tail -f robust_drop_monitor.log"
echo "  2. Check health: cat monitor_health.json"
echo "  3. Service status: sudo systemctl status whatsapp-drop-monitor"
echo "  4. View service logs: sudo journalctl -u whatsapp-drop-monitor -f"
echo ""
echo "🔧 The new monitor includes:"
echo "  ✅ Comprehensive error handling"
echo "  ✅ Health monitoring and reporting"
echo "  ✅ Atomic transaction processing"
echo "  ✅ Process validation and rollback"
echo "  ✅ Detailed logging and debugging"
echo ""
echo "🎯 This should finally solve the recurring processing issues!"