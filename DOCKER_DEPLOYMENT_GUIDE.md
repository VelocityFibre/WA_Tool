# 🐳 Docker Deployment Guide - Privacy-Filtered WA Tool

**Date**: October 2nd, 2025  
**Architecture**: Hybrid SQLite (sessions) + PostgreSQL (business data)  
**Deployment**: Local → DigitalOcean VPS

---

## 📋 **QUICK START - LOCAL DEPLOYMENT**

### **Step 1: Setup Environment**
```bash
# Create environment file
cp .env.example .env
vi .env  # Configure your database URLs and credentials

# Create data directories
mkdir -p docker-data/{whatsapp-sessions,bridge-logs,monitor-logs}

# Copy Google credentials (if you have them)
cp /path/to/your/service-account.json ./credentials.json
```

### **Step 2: Deploy with Docker**
```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View WhatsApp Bridge logs (for QR code)
docker-compose logs -f whatsapp-bridge
```

### **Step 3: Connect WhatsApp**
```bash
# Watch for QR code in logs
docker-compose logs whatsapp-bridge

# Or access via web browser
open http://localhost:8080
```

### **Step 4: Monitor Services**
```bash
# Check all service logs
docker-compose logs -f

# Check specific service
docker-compose logs -f drop-monitor

# Restart a service
docker-compose restart qa-monitor
```

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues:**

**WhatsApp Bridge won't start:**
```bash
# Check if port is in use
sudo netstat -tlnp | grep :8080

# If port is busy, stop old services
pkill -f whatsapp-bridge
docker-compose up -d
```

**Python monitors can't connect:**
```bash
# Check bridge health
curl http://localhost:8080

# Check network connectivity
docker-compose exec drop-monitor curl http://whatsapp-bridge:8080
```

**Missing credentials:**
```bash
# Check if Google credentials are mounted
docker-compose exec drop-monitor ls -la /app/credentials.json

# If missing, copy and restart
cp your-credentials.json ./credentials.json
docker-compose restart drop-monitor qa-monitor
```

---

## 🚀 **MIGRATION TO DIGITALOCEAN VPS**

### **Phase 1: VPS Setup**

**1. Create DigitalOcean Droplet:**
- **Size**: 2 vCPU, 4GB RAM, 80GB SSD ($24/month)
- **OS**: Ubuntu 22.04 LTS
- **Datacenter**: Closest to your location
- **SSH Keys**: Add your public key

**2. Initial Server Setup:**
```bash
# Connect to your VPS
ssh root@your-vps-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create deployment directory
mkdir -p /opt/wa-tool
cd /opt/wa-tool
```

### **Phase 2: Deploy Code to VPS**

**Option A: Git Clone (Recommended)**
```bash
# On VPS
git clone https://github.com/your-username/WA_Tool.git .
# Or upload your code via SCP/SFTP
```

**Option B: Direct Copy from Local**
```bash
# From your local machine
rsync -avz --progress /home/louisdup/VF/Apps/WA_Tool/ root@your-vps-ip:/opt/wa-tool/

# Exclude unnecessary files
rsync -avz --progress --exclude='docker-data/' --exclude='*.log' /home/louisdup/VF/Apps/WA_Tool/ root@your-vps-ip:/opt/wa-tool/
```

### **Phase 3: Configure VPS Environment**
```bash
# On VPS - Setup environment
cp .env.example .env
vi .env  # Update with your configurations

# Create data directories
mkdir -p docker-data/{whatsapp-sessions,bridge-logs,monitor-logs}

# Copy Google credentials
scp your-credentials.json root@your-vps-ip:/opt/wa-tool/credentials.json
```

### **Phase 4: Migrate WhatsApp Session**

**Option A: Copy Session Data (Recommended)**
```bash
# From local machine, copy WhatsApp session
scp -r docker-data/whatsapp-sessions/ root@your-vps-ip:/opt/wa-tool/docker-data/

# On VPS, deploy with existing session
docker-compose up -d
```

**Option B: Fresh WhatsApp Connection**
```bash
# On VPS, start fresh (will need new QR code scan)
docker-compose up -d
docker-compose logs -f whatsapp-bridge  # Watch for QR code
```

### **Phase 5: Configure Domain & SSL (Optional)**
```bash
# Install Nginx reverse proxy
apt install nginx certbot python3-certbot-nginx

# Configure Nginx for your domain
vi /etc/nginx/sites-available/wa-tool

# Example Nginx config:
server {
    listen 80;
    server_name yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site and get SSL
ln -s /etc/nginx/sites-available/wa-tool /etc/nginx/sites-enabled/
certbot --nginx -d yourdomain.com
nginx -s reload
```

---

## 📊 **MONITORING & MAINTENANCE**

### **Service Health Checks:**
```bash
# Check all services
docker-compose ps

# Check service health
docker-compose exec whatsapp-bridge wget -qO- http://localhost:8080

# Monitor resource usage
docker stats
```

### **Log Management:**
```bash
# Rotate logs to prevent disk space issues
echo '{"log-driver":"json-file","log-opts":{"max-size":"10m","max-file":"3"}}' > /etc/docker/daemon.json
systemctl restart docker

# View recent logs
docker-compose logs --tail=100 -f
```

### **Backup Strategy:**
```bash
# Backup WhatsApp sessions (critical!)
tar -czf backup-sessions-$(date +%Y%m%d).tar.gz docker-data/whatsapp-sessions/

# Backup to external storage
rsync -avz docker-data/ backup-server:/backups/wa-tool/
```

### **Updates & Maintenance:**
```bash
# Update containers
docker-compose pull
docker-compose up -d

# Clean up unused images
docker system prune -a
```

---

## 💰 **COSTS & OPTIMIZATION**

### **DigitalOcean Monthly Costs:**
- **Droplet (2vCPU, 4GB)**: $24/month
- **Backup (optional)**: $2.40/month (10% of droplet cost)
- **Domain**: $12/year
- **Total**: ~$26/month

### **Cost Optimization:**
```bash
# Use smaller droplet for testing
# 1 vCPU, 2GB RAM = $12/month

# Monitor resource usage
docker stats
htop
df -h
```

---

## 🔒 **SECURITY CHECKLIST**

### **VPS Security:**
```bash
# Change SSH port (optional)
vi /etc/ssh/sshd_config
# Port 2222

# Configure UFW firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Disable root login (after creating user)
adduser deploy
usermod -aG docker deploy
```

### **Application Security:**
- ✅ Privacy filter active (only monitored groups)
- ✅ Environment variables for secrets
- ✅ No hardcoded credentials
- ✅ Regular security updates

---

## ✅ **DEPLOYMENT CHECKLIST**

### **Local Testing:**
- [ ] Docker containers build successfully
- [ ] WhatsApp Bridge connects and shows QR code
- [ ] Privacy filter working (only 3 groups in database)
- [ ] Drop monitor detecting new messages
- [ ] QA monitor sending feedback
- [ ] All logs are accessible

### **VPS Deployment:**
- [ ] DigitalOcean droplet created and accessible
- [ ] Docker and Docker Compose installed
- [ ] Code deployed to VPS
- [ ] Environment variables configured
- [ ] WhatsApp session migrated or reconnected
- [ ] All services healthy and running
- [ ] Domain configured (optional)
- [ ] SSL certificate installed (optional)
- [ ] Backup strategy implemented

---

## 🎯 **NEXT STEPS**

1. **Test locally first**: `docker-compose up -d`
2. **Verify privacy filter**: Check only 3 groups in database
3. **Create DigitalOcean account**: Sign up if you don't have one
4. **Deploy to VPS**: Follow migration guide above
5. **Monitor and optimize**: Use monitoring tools

**Ready to start with local deployment?** 🚀