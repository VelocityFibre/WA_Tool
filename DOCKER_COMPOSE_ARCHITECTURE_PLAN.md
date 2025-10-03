# 🐳 Docker Compose Architecture Plan for WA Tool Services

**Date**: October 2nd, 2025  
**Status**: PLANNING PHASE - To be implemented  
**Goal**: Create portable, manageable service architecture for local & remote deployment

---

## 🎯 **ARCHITECTURE OVERVIEW**

### **Service Structure:**
```
WA_Tool/
├── docker-compose.yml           # Main orchestration file
├── .env                        # Environment variables (sensitive data)
├── .env.example               # Template for environment setup
├── services/
│   ├── whatsapp-bridge/       # WhatsApp Bridge service
│   │   ├── Dockerfile
│   │   └── config/
│   ├── qa-monitor/            # QA Sheets Monitor service  
│   │   ├── Dockerfile
│   │   └── src/
│   ├── realtime-monitor/      # Realtime Drop Monitor service
│   │   ├── Dockerfile  
│   │   └── src/
│   └── message-monitor/       # WhatsApp Message Monitor service
│       ├── Dockerfile
│       └── src/
├── data/                      # Persistent data volumes
│   ├── whatsapp-sessions/     # WhatsApp session data
│   ├── databases/             # SQLite databases
│   └── logs/                  # All service logs
├── scripts/                   # Management scripts
│   ├── start.sh              # Start all services
│   ├── stop.sh               # Stop all services
│   ├── logs.sh               # View logs
│   ├── status.sh             # Check service status
│   └── backup.sh             # Backup configuration
└── README.md                 # Setup & deployment instructions
```

---

## 🔧 **SERVICE DEFINITIONS**

### **1. WhatsApp Bridge Service**
- **Purpose**: Handle WhatsApp Web connection and API
- **Port**: 8080 (internal), configurable external
- **Dependencies**: None (base service)
- **Restart**: always
- **Health Check**: HTTP endpoint ping

### **2. QA Monitor Service**  
- **Purpose**: Monitor Google Sheets for incomplete flags, send feedback
- **Dependencies**: WhatsApp Bridge (healthy)
- **Environment**: Google Sheets credentials, rate limiting config
- **Restart**: on-failure (max 3 attempts)
- **Safety Features**: PID locking, rate limiting, duplicate detection

### **3. Realtime Monitor Service**
- **Purpose**: Monitor WhatsApp for new drop numbers, sync to database/sheets
- **Dependencies**: WhatsApp Bridge (healthy)  
- **Environment**: Database credentials, Google Sheets API
- **Restart**: on-failure (max 3 attempts)
- **Safety Features**: Duplicate detection, batch processing

### **4. Message Monitor Service**
- **Purpose**: Process WhatsApp messages for specific groups
- **Dependencies**: WhatsApp Bridge (healthy)
- **Environment**: Group JIDs, processing rules
- **Restart**: on-failure (max 3 attempts)

---

## 📋 **IMPLEMENTATION PHASES**

### **Phase 1: Basic Structure (30 minutes)**
1. Create directory structure
2. Write base docker-compose.yml
3. Create environment template (.env.example)
4. Set up basic logging and volumes

### **Phase 2: WhatsApp Bridge Container (20 minutes)**
1. Create Dockerfile for WhatsApp Bridge
2. Configure port mapping and health checks
3. Set up session persistence volume
4. Test bridge connectivity

### **Phase 3: Python Services Containers (45 minutes)**
1. Create unified Python Dockerfile (base image)
2. Configure QA Monitor service with safety features
3. Configure Realtime Monitor service
4. Configure Message Monitor service
5. Implement inter-service dependencies

### **Phase 4: Safety & Management (30 minutes)**
1. Implement rate limiting across services
2. Add PID locking and duplicate detection
3. Create management scripts (start/stop/status/logs)
4. Set up centralized logging configuration
5. Configure restart policies and health checks

### **Phase 5: Testing & Documentation (20 minutes)**
1. Test full startup/shutdown cycle
2. Verify service dependencies work correctly
3. Test safety features (rate limiting, duplicate detection)
4. Create deployment documentation
5. Test backup/restore procedures

---

## 🛡️ **SAFETY FEATURES INTEGRATION**

### **Rate Limiting Configuration:**
```yaml
environment:
  - RATE_LIMIT_MESSAGES_PER_MINUTE=2
  - RATE_LIMIT_MESSAGES_PER_HOUR=20
  - RATE_LIMIT_MESSAGES_PER_DAY=100
  - COOLDOWN_SAME_DROP_SECONDS=3600
```

### **Database Integration:**
- PostgreSQL connection for feedback tracking
- SQLite volume for WhatsApp message storage
- Shared volume for service state synchronization

### **Inter-Service Communication:**
- Services wait for WhatsApp Bridge to be healthy
- Shared network for internal communication
- External ports only where necessary

---

## 🔄 **DEPLOYMENT WORKFLOW**

### **Local Development:**
```bash
cd /home/louisdup/VF/Apps/WA_Tool
cp .env.example .env          # Configure environment
docker-compose up -d          # Start all services
./scripts/status.sh           # Check status
docker-compose logs -f        # Monitor logs
```

### **Remote Server Deployment:**
```bash
# Package for deployment
tar --exclude='data/logs/*' --exclude='data/whatsapp-sessions/*' \
    -czf wa-tool-deploy.tar.gz WA_Tool/

# On remote server
scp wa-tool-deploy.tar.gz user@server:/opt/
ssh user@server "cd /opt && tar -xzf wa-tool-deploy.tar.gz"
ssh user@server "cd /opt/WA_Tool && cp .env.example .env"
# Edit .env with server-specific values
ssh user@server "cd /opt/WA_Tool && docker-compose up -d"
```

---

## 🔧 **CONFIGURATION DECISIONS NEEDED**

### **1. Base Python Image**
**Question**: Should we use:
- `python:3.11-slim` (smaller, faster)
- `python:3.11` (includes more tools)
- Custom base with UV pre-installed?

**Recommendation**: python:3.11-slim with UV installed for consistency

### **2. Volume Strategy**
**Question**: How should we handle data persistence?
- Named Docker volumes (portable)
- Bind mounts to host directories (easier backup)
- Mix of both?

**Recommendation**: Named volumes for databases/sessions, bind mounts for logs/config

### **3. Network Configuration**
**Question**: Networking approach:
- Single Docker network (internal communication)
- Bridge network with port exposure
- Host networking?

**Recommendation**: Single internal network, minimal port exposure

### **4. Environment Management**
**Question**: How to handle sensitive data?
- Single .env file
- Separate files per service
- Docker secrets?

**Recommendation**: Single .env with clear sections for each service

### **5. Restart Policies**
**Question**: How aggressive should auto-restart be?
- `always` (keeps trying forever)
- `on-failure:3` (try 3 times then stop)
- `unless-stopped` (restart unless manually stopped)

**Recommendation**: `unless-stopped` for bridge, `on-failure:3` for monitors

---

## 📊 **RESOURCE PLANNING**

### **Expected Resource Usage:**
- WhatsApp Bridge: 50MB RAM, minimal CPU
- QA Monitor: 100MB RAM, low CPU (periodic spikes)
- Realtime Monitor: 80MB RAM, low CPU
- Message Monitor: 60MB RAM, low CPU
- **Total**: ~300MB RAM, 1 CPU core adequate

### **Scaling Considerations:**
- QA Monitor can scale horizontally with proper locking
- Message Monitor can be split by group
- Bridge must remain single instance

---

## ✅ **SUCCESS CRITERIA**

### **Functional Requirements:**
- [ ] Single command start/stop all services
- [ ] Services restart automatically on failure
- [ ] Zero-downtime deployment possible
- [ ] Complete logs accessible via Docker commands
- [ ] Easy backup/restore of all data and configuration

### **Safety Requirements:**
- [ ] Rate limiting prevents message spam
- [ ] PID locking prevents duplicate processes
- [ ] Service health checks prevent cascading failures
- [ ] Graceful shutdown preserves data integrity
- [ ] Configuration validation on startup

### **Operational Requirements:**
- [ ] Works identically on laptop and remote server
- [ ] Simple deployment process (< 5 commands)
- [ ] Clear status monitoring and troubleshooting
- [ ] Automated log rotation and cleanup
- [ ] Resource usage monitoring and limits

---

## 🚨 **RISK MITIGATION**

### **Identified Risks:**
1. **WhatsApp Bridge session loss** → Persistent volume for session data
2. **Service dependency failures** → Health checks and restart policies  
3. **Resource exhaustion** → Memory limits and monitoring
4. **Configuration drift** → Version controlled .env.example template
5. **Data loss during deployment** → Backup scripts and volume persistence

### **Testing Strategy:**
1. Test on local environment first
2. Simulate service failures (kill containers)
3. Test deployment to fresh system
4. Verify backup/restore procedures
5. Load test with rate limiting

---

**Next Steps**: Review this plan and confirm approach before implementation begins.