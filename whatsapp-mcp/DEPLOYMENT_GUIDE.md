# Production Deployment Guide

## Overview

This guide covers deploying the WhatsApp Quality Control System in production environments with reliability, monitoring, and maintenance best practices.

## 🚀 Production Architecture

### System Components
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  WhatsApp Web   │◄──►│  WhatsApp Bridge │◄──►│   SQLite DB     │
│     API         │    │   (Go Process)   │    │  (Messages)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│   MCP Server     │    │  Monitor State  │
│  (Claude AI)    │    │ (Python Process) │    │     (JSON)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  VF_Drops Web   │◄──►│ Drop Monitor     │◄──►│ Neon PostgreSQL │
│   Dashboard     │    │ (Python Service) │    │ (QA Database)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Pre-deployment Checklist

### Infrastructure Requirements
- [ ] **Server**: Linux server (Ubuntu 20.04+ recommended)
- [ ] **Memory**: Minimum 4GB RAM, 8GB+ recommended
- [ ] **Storage**: 50GB+ SSD storage for message history
- [ ] **Network**: Stable internet connection
- [ ] **Database**: Neon PostgreSQL instance configured
- [ ] **Domain**: Optional - for external access with reverse proxy

### Software Dependencies
- [ ] **Go 1.19+**: For WhatsApp bridge
- [ ] **Python 3.11+**: For MCP server and monitoring
- [ ] **UV Package Manager**: Latest version
- [ ] **Node.js 18+**: For VF_Drops frontend
- [ ] **FFmpeg**: For audio message support
- [ ] **Systemd**: For service management

### Security Prerequisites
- [ ] **Firewall**: Configure appropriate ports
- [ ] **SSL Certificates**: If exposing externally
- [ ] **Database Encryption**: Neon SSL configured
- [ ] **Backup Strategy**: Database and message backups
- [ ] **User Permissions**: Non-root user for services

## 🔧 Installation Process

### 1. System Preparation
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y git curl wget build-essential

# Create application user
sudo useradd -m -s /bin/bash whatsapp-qa
sudo usermod -aG sudo whatsapp-qa

# Switch to application user
sudo su - whatsapp-qa
```

### 2. Install Dependencies
```bash
# Install Go
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc

# Install Python and UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install FFmpeg
sudo apt install -y ffmpeg
```

### 3. Deploy Application
```bash
# Clone repository
git clone <your-repo-url> /opt/whatsapp-qa
cd /opt/whatsapp-qa

# Set permissions
sudo chown -R whatsapp-qa:whatsapp-qa /opt/whatsapp-qa

# Build WhatsApp bridge
cd whatsapp-bridge
go mod tidy
go build -o whatsapp-bridge main.go

# Setup Python environment
cd ../whatsapp-mcp-server
uv sync

# Install VF_Drops frontend dependencies
cd ../../VF_Drops
npm install
npm run build
```

### 4. Configuration
```bash
# Create environment configuration
cat > /opt/whatsapp-qa/.env << 'EOF'
# Production Environment Variables
NODE_ENV=production
DATABASE_URL=postgresql://user:pass@host:5432/database
WHATSAPP_GROUP_JID=120363418298130331@g.us
MONITOR_INTERVAL=15
LOG_LEVEL=info
EOF

# Set appropriate permissions
chmod 600 /opt/whatsapp-qa/.env
```

## 🔄 Service Configuration

### 1. WhatsApp Bridge Service
```bash
# Create systemd service
sudo tee /etc/systemd/system/whatsapp-bridge.service << 'EOF'
[Unit]
Description=WhatsApp Bridge Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=whatsapp-qa
Group=whatsapp-qa
WorkingDirectory=/opt/whatsapp-qa/whatsapp-bridge
ExecStart=/opt/whatsapp-qa/whatsapp-bridge/whatsapp-bridge
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Resource limits
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF
```

### 2. MCP Server Service
```bash
sudo tee /etc/systemd/system/whatsapp-mcp.service << 'EOF'
[Unit]
Description=WhatsApp MCP Server
After=network.target whatsapp-bridge.service
Wants=network.target
Requires=whatsapp-bridge.service

[Service]
Type=simple
User=whatsapp-qa
Group=whatsapp-qa
WorkingDirectory=/opt/whatsapp-qa/whatsapp-mcp-server
ExecStart=/home/whatsapp-qa/.local/bin/uv run main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
EnvironmentFile=/opt/whatsapp-qa/.env

# Resource limits
MemoryMax=512M
CPUQuota=25%

[Install]
WantedBy=multi-user.target
EOF
```

### 3. Quality Control Monitor Service
```bash
sudo tee /etc/systemd/system/whatsapp-qa-monitor.service << 'EOF'
[Unit]
Description=WhatsApp QA Photo Review Monitor
After=network.target whatsapp-bridge.service
Wants=network.target
Requires=whatsapp-bridge.service

[Service]
Type=simple
User=whatsapp-qa
Group=whatsapp-qa
WorkingDirectory=/opt/whatsapp-qa/whatsapp-mcp-server
ExecStart=/home/whatsapp-qa/.local/bin/uv run python realtime_drop_monitor.py --interval 15
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal
EnvironmentFile=/opt/whatsapp-qa/.env

# Resource limits
MemoryMax=256M
CPUQuota=10%

[Install]
WantedBy=multi-user.target
EOF
```

### 4. VF_Drops Frontend Service
```bash
sudo tee /etc/systemd/system/vf-drops.service << 'EOF'
[Unit]
Description=VF Drops Quality Control Dashboard
After=network.target

[Service]
Type=simple
User=whatsapp-qa
Group=whatsapp-qa
WorkingDirectory=/opt/whatsapp-qa/../VF_Drops
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
Environment=NODE_ENV=production
Environment=PORT=3000

# Resource limits
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF
```

### 5. Enable and Start Services
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services for auto-start
sudo systemctl enable whatsapp-bridge.service
sudo systemctl enable whatsapp-mcp.service  
sudo systemctl enable whatsapp-qa-monitor.service
sudo systemctl enable vf-drops.service

# Start services
sudo systemctl start whatsapp-bridge.service
sudo systemctl start whatsapp-mcp.service
sudo systemctl start whatsapp-qa-monitor.service
sudo systemctl start vf-drops.service

# Check status
sudo systemctl status whatsapp-bridge.service
sudo systemctl status whatsapp-mcp.service
sudo systemctl status whatsapp-qa-monitor.service
sudo systemctl status vf-drops.service
```

## 🔒 Security Hardening

### 1. Firewall Configuration
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (adjust port as needed)
sudo ufw allow 22

# Allow internal services only
sudo ufw allow from 10.0.0.0/8 to any port 3000
sudo ufw allow from 192.168.0.0/16 to any port 3000
sudo ufw allow from 172.16.0.0/12 to any port 3000

# Check status
sudo ufw status verbose
```

### 2. File Permissions
```bash
# Set strict permissions on configuration files
chmod 600 /opt/whatsapp-qa/.env
chmod 700 /opt/whatsapp-qa/whatsapp-bridge/store/
chmod 600 /opt/whatsapp-qa/whatsapp-mcp-server/monitor_state.json

# Set ownership
sudo chown -R whatsapp-qa:whatsapp-qa /opt/whatsapp-qa
```

### 3. Log Rotation
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/whatsapp-qa << 'EOF'
/opt/whatsapp-qa/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 whatsapp-qa whatsapp-qa
    postrotate
        systemctl reload whatsapp-bridge whatsapp-mcp whatsapp-qa-monitor vf-drops
    endscript
}
EOF
```

## 📊 Monitoring & Logging

### 🔍 Real-time System Monitoring Setup

The system includes a comprehensive monitoring dashboard with real-time health checks:

#### 1. Web-based Monitoring Configuration
```bash
# Ensure VF_Drops frontend is configured for monitoring
cd /opt/whatsapp-qa/../VF_Drops

# Verify system status API endpoint is accessible
curl http://localhost:3000/api/system-status | jq '.overall'
```

**Monitoring Features:**
- **Header Status Indicator**: Real-time system health badge (updates every 60s)
- **System Monitor Dashboard**: Detailed component breakdown (updates every 30s)
- **Automatic Refresh**: No manual intervention required
- **Component Tracking**: Monitors both systemd services and running processes

#### 2. Service Detection Configuration
The monitoring system automatically detects services using hybrid approach:

```bash
# Test systemd service detection
systemctl is-active whatsapp-bridge.service
systemctl is-active whatsapp-mcp.service
systemctl is-active whatsapp-qa-monitor.service

# Test process detection (fallback method)
ps aux | grep -E "whatsapp-bridge|main\.go" | grep -v grep
ps aux | grep -E "uv run main\.py|main\.py" | grep -v grep
ps aux | grep -E "realtime_drop_monitor\.py" | grep -v grep
```

#### 3. Database Health Monitoring Setup
```bash
# Configure database health checks
# SQLite WhatsApp messages
sqlite3 /opt/whatsapp-qa/whatsapp-bridge/store/messages.db "SELECT COUNT(*) FROM messages WHERE timestamp > datetime('now', '-1 hour')"

# PostgreSQL connectivity test
curl http://localhost:3000/api/installations?limit=1

# Monitor state file freshness
stat /opt/whatsapp-qa/whatsapp-mcp-server/monitor_state.json
```

#### 4. Monitoring API Integration
```bash
# Set up monitoring endpoint health checks
tee /opt/whatsapp-qa/scripts/monitoring-check.sh << 'EOF'
#!/bin/bash

# Get overall system status
STATUS=$(curl -s http://localhost:3000/api/system-status | jq -r '.overall')

case $STATUS in
    "healthy")
        echo "✅ System Status: HEALTHY"
        ;;
    "warning")
        echo "⚠️ System Status: WARNING - Check dashboard for details"
        logger "WhatsApp QA System Status: WARNING"
        ;;
    "error")
        echo "❌ System Status: ERROR - Immediate attention required"
        logger "WhatsApp QA System Status: CRITICAL ERROR"
        # Send critical alert
        ;;
    *)
        echo "❓ System Status: UNKNOWN - Monitoring API may be down"
        logger "WhatsApp QA System Status: Monitoring API unavailable"
        ;;
esac

# Check individual components if not healthy
if [ "$STATUS" != "healthy" ]; then
    echo "Component Details:"
    curl -s http://localhost:3000/api/system-status | jq '.services | to_entries[] | "\(.key): \(.value.status)"'
fi
EOF

chmod +x /opt/whatsapp-qa/scripts/monitoring-check.sh
```

### 2. Legacy Health Monitoring (Fallback)
```bash
# Create traditional health check script
tee /opt/whatsapp-qa/scripts/health-check.sh << 'EOF'
#!/bin/bash

# Check service status
services=("whatsapp-bridge" "whatsapp-mcp" "whatsapp-qa-monitor" "vf-drops")

for service in "${services[@]}"; do
    if ! systemctl is-active --quiet "${service}.service"; then
        echo "CRITICAL: ${service} service is not running"
        # Send alert (email, Slack, etc.)
        logger "WhatsApp QA Health Check: ${service} service failed"
    else
        echo "OK: ${service} service is running"
    fi
done

# Check database connectivity
if ! curl -f http://localhost:3000/api/installations > /dev/null 2>&1; then
    echo "CRITICAL: Database connection failed"
    logger "WhatsApp QA Health Check: Database connection failed"
else
    echo "OK: Database connection successful"
fi

# Check WhatsApp authentication
if ! pgrep -f "whatsapp-bridge" > /dev/null; then
    echo "WARNING: WhatsApp bridge process not found"
    logger "WhatsApp QA Health Check: WhatsApp bridge not running"
fi
EOF

chmod +x /opt/whatsapp-qa/scripts/health-check.sh
```

### 3. Automated Health Checks
```bash
# Set up automated monitoring (preferred method)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/whatsapp-qa/scripts/monitoring-check.sh >> /opt/whatsapp-qa/logs/monitoring.log 2>&1") | crontab -

# Set up traditional health checks (fallback)
(crontab -l 2>/dev/null; echo "*/10 * * * * /opt/whatsapp-qa/scripts/health-check.sh >> /opt/whatsapp-qa/logs/health-check.log 2>&1") | crontab -

# Daily monitoring summary
(crontab -l 2>/dev/null; echo "0 8 * * * /opt/whatsapp-qa/scripts/daily-monitoring-report.sh") | crontab -
```

### 4. Monitoring Dashboard Access
```bash
# Create monitoring dashboard shortcut
tee /opt/whatsapp-qa/scripts/open-monitoring.sh << 'EOF'
#!/bin/bash
echo "Access System Monitor Dashboard:"
echo "URL: http://localhost:3000"
echo "Tab: System Monitor"
echo ""
echo "Quick Status Check:"
curl -s http://localhost:3000/api/system-status | jq '{overall: .overall, services: (.services | keys)}'
EOF

chmod +x /opt/whatsapp-qa/scripts/open-monitoring.sh
```

### 3. Log Monitoring
```bash
# Monitor specific patterns in logs
tee /opt/whatsapp-qa/scripts/log-monitor.sh << 'EOF'
#!/bin/bash

# Monitor for errors in logs
journalctl -u whatsapp-bridge.service --since "5 minutes ago" | grep -i "error\|failed\|critical" && {
    echo "Errors detected in whatsapp-bridge service"
    # Send alert
}

journalctl -u whatsapp-qa-monitor.service --since "5 minutes ago" | grep -i "error\|failed\|critical" && {
    echo "Errors detected in QA monitor service"
    # Send alert
}
EOF

chmod +x /opt/whatsapp-qa/scripts/log-monitor.sh
```

## 🔄 Backup & Recovery

### 1. Database Backup
```bash
# Create backup script
tee /opt/whatsapp-qa/scripts/backup-db.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/whatsapp-qa/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p ${BACKUP_DIR}

# Backup SQLite database
cp /opt/whatsapp-qa/whatsapp-bridge/store/messages.db ${BACKUP_DIR}/messages_${DATE}.db
cp /opt/whatsapp-qa/whatsapp-bridge/store/whatsapp.db ${BACKUP_DIR}/whatsapp_${DATE}.db

# Backup monitor state
cp /opt/whatsapp-qa/whatsapp-mcp-server/monitor_state.json ${BACKUP_DIR}/monitor_state_${DATE}.json

# Backup Neon database (if applicable)
# pg_dump $DATABASE_URL > ${BACKUP_DIR}/neon_backup_${DATE}.sql

# Cleanup old backups (keep 30 days)
find ${BACKUP_DIR} -name "*.db" -mtime +30 -delete
find ${BACKUP_DIR} -name "*.json" -mtime +30 -delete

echo "Backup completed: ${DATE}"
EOF

chmod +x /opt/whatsapp-qa/scripts/backup-db.sh

# Schedule daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/whatsapp-qa/scripts/backup-db.sh >> /opt/whatsapp-qa/logs/backup.log 2>&1") | crontab -
```

### 2. Configuration Backup
```bash
# Backup system configuration
tee /opt/whatsapp-qa/scripts/backup-config.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="/opt/whatsapp-qa/config-backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p ${BACKUP_DIR}

# Backup systemd services
sudo cp /etc/systemd/system/whatsapp-*.service ${BACKUP_DIR}/
sudo cp /etc/systemd/system/vf-drops.service ${BACKUP_DIR}/

# Backup environment configuration
cp /opt/whatsapp-qa/.env ${BACKUP_DIR}/.env_${DATE}

# Create tar archive
tar -czf ${BACKUP_DIR}/config_backup_${DATE}.tar.gz -C /opt/whatsapp-qa .

echo "Configuration backup completed: ${DATE}"
EOF

chmod +x /opt/whatsapp-qa/scripts/backup-config.sh
```

## 🔄 Update & Maintenance

### 1. Rolling Updates
```bash
# Create update script
tee /opt/whatsapp-qa/scripts/update-system.sh << 'EOF'
#!/bin/bash

set -e

echo "Starting system update..."

# Pull latest code
cd /opt/whatsapp-qa
git pull origin main

# Update WhatsApp bridge
cd whatsapp-bridge
go mod tidy
go build -o whatsapp-bridge.new main.go

# Update Python dependencies  
cd ../whatsapp-mcp-server
uv sync

# Update frontend
cd ../../VF_Drops
npm install
npm run build

# Rolling restart services
echo "Restarting services..."
sudo systemctl restart whatsapp-qa-monitor.service
sleep 10

sudo systemctl restart whatsapp-mcp.service
sleep 10

# Replace binary and restart bridge
cd /opt/whatsapp-qa/whatsapp-bridge
mv whatsapp-bridge whatsapp-bridge.old
mv whatsapp-bridge.new whatsapp-bridge
sudo systemctl restart whatsapp-bridge.service
sleep 10

sudo systemctl restart vf-drops.service

echo "Update completed successfully"
EOF

chmod +x /opt/whatsapp-qa/scripts/update-system.sh
```

### 2. System Maintenance
```bash
# Weekly maintenance script
tee /opt/whatsapp-qa/scripts/maintenance.sh << 'EOF'
#!/bin/bash

echo "Starting weekly maintenance..."

# Clean old logs
journalctl --vacuum-time=30d

# Clean temporary files
rm -rf /tmp/whatsapp-*
rm -rf /opt/whatsapp-qa/whatsapp-mcp-server/.uv/cache/

# Update system packages
sudo apt update && sudo apt upgrade -y

# Restart services for memory cleanup
sudo systemctl restart whatsapp-qa-monitor.service
sudo systemctl restart whatsapp-mcp.service

echo "Maintenance completed"
EOF

chmod +x /opt/whatsapp-qa/scripts/maintenance.sh

# Schedule weekly maintenance
(crontab -l 2>/dev/null; echo "0 3 * * 0 /opt/whatsapp-qa/scripts/maintenance.sh >> /opt/whatsapp-qa/logs/maintenance.log 2>&1") | crontab -
```

## 🚨 Troubleshooting

### Common Issues

#### WhatsApp Authentication Problems
```bash
# Check WhatsApp bridge logs
journalctl -u whatsapp-bridge.service -f

# Reset authentication
sudo systemctl stop whatsapp-bridge.service
rm -f /opt/whatsapp-qa/whatsapp-bridge/store/whatsapp.db
sudo systemctl start whatsapp-bridge.service

# Check for QR code in logs
journalctl -u whatsapp-bridge.service --since "5 minutes ago"
```

#### Service Connection Issues
```bash
# Check service dependencies
systemctl list-dependencies whatsapp-qa-monitor.service

# Check network connectivity
netstat -tlnp | grep -E ':(3000|8080)'
ss -tlnp | grep -E ':(3000|8080)'

# Test database connection
curl -f http://localhost:3000/api/installations
```

#### Performance Issues
```bash
# Check resource usage
systemctl status whatsapp-bridge.service --no-pager -l
systemctl status whatsapp-qa-monitor.service --no-pager -l

# Monitor system resources
top -p $(pgrep -f "whatsapp\|uv run")
free -h
df -h

# Check database performance
tail -f /opt/whatsapp-qa/logs/database.log
```

## 📈 Performance Optimization

### Database Optimization
```bash
# SQLite optimization
echo "PRAGMA optimize;" | sqlite3 /opt/whatsapp-qa/whatsapp-bridge/store/messages.db

# Monitor database size
du -sh /opt/whatsapp-qa/whatsapp-bridge/store/
```

### Service Tuning
```bash
# Adjust systemd resource limits based on usage
sudo systemctl edit whatsapp-qa-monitor.service

# Add content:
[Service]
MemoryMax=512M
CPUQuota=20%
```

## 📞 Production Support

### Emergency Procedures
1. **Service Outage**: Check systemd service status, restart if needed
2. **Database Issues**: Restore from latest backup
3. **WhatsApp Auth Failure**: Re-authenticate using QR code
4. **Memory Issues**: Restart services, check for memory leaks

### Contact Information
- **System Admin**: Monitor service status and logs
- **Database Admin**: Handle database connectivity issues  
- **WhatsApp Admin**: Manage WhatsApp authentication and groups

### Escalation Process
1. **Level 1**: Automated alerts and basic troubleshooting
2. **Level 2**: Manual intervention and service restarts
3. **Level 3**: Code changes, configuration updates, or infrastructure changes

This production deployment guide ensures reliable, secure, and maintainable operation of the WhatsApp Quality Control System in production environments.