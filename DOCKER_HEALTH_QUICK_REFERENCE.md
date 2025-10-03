# Docker Health Check Quick Reference

**Date:** October 3, 2025

## Quick Status Check Commands

```bash
# Check all WA containers
docker ps --filter "name=wa-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Run comprehensive health check
python3 system_health_check.py

# Check specific container logs
docker logs wa-bridge-privacy --tail 10
docker logs wa-drop-monitor --tail 10
docker logs wa-qa-monitor --tail 10
```

## Expected Healthy Output

### Container Status (should show):
```
NAMES                STATUS         PORTS
wa-mohadin-monitor   Up X minutes   
wa-qa-monitor        Up X minutes   
wa-drop-monitor      Up X minutes   
wa-bridge-privacy    Up X minutes   0.0.0.0:8080->8080/tcp
```

### System Health Check (should show):
```
🐳 DOCKER CONTAINER STATUS:
  ✅ wa-bridge-privacy: Up X minutes
  ✅ wa-drop-monitor: Up X minutes
  ✅ wa-qa-monitor: Up X minutes
```

## Troubleshooting

### If Containers Show "Unhealthy" Again:

1. **Check actual functionality first**
   ```bash
   # Test WhatsApp Bridge API
   curl -I http://localhost:8080
   
   # Check recent logs for errors
   docker logs wa-bridge-privacy --tail 20
   ```

2. **Restart services if needed**
   ```bash
   docker-compose restart
   # or
   docker-compose down && docker-compose up -d
   ```

3. **Disable health checks again**
   ```bash
   # Verify healthcheck: disable: true is in docker-compose.yml
   grep -A2 "healthcheck:" docker-compose.yml
   ```

## Portainer Access

- **URL**: https://172.20.10.2:9443
- **Bypass certificate warning**: Click "Advanced" → "Proceed"
- **Quick container actions**: Start/Stop/Restart containers with one click

## Key Files

- `docker-compose.yml` - Container configuration with disabled health checks
- `system_health_check.py` - Comprehensive system status checker
- `DOCKER_HEALTH_CHECK_FIXES.md` - Full documentation of fixes

---

**Remember**: "Unhealthy" containers might still be working perfectly. Always check actual functionality, not just health check status!