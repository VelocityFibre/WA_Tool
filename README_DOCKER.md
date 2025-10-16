# WA_Tool Microservices - Docker Deployment

## Overview

The WA_Tool has been refactored into a microservices architecture with containerized deployment using Docker and Docker Compose. Each WhatsApp group monitoring service runs in isolation with dedicated health checks and can be managed independently through Portainer.

## Architecture

### Services

- **Mohadin Service** (`mohadin-service`): Port 8081 - Parallel testing mode (safe monitoring)
- **Velo Test Service** (`velo-test-service`): Port 8082 - Production mode (live operations)
- **WhatsApp Bridge**: Port 8080 - Shared communication bridge
- **Portainer**: Port 9443 - Container management interface

### Key Features

- **Isolated Services**: Each group runs in its own container
- **Health Monitoring**: Built-in health checks for all services
- **Port Management**: Automatic port allocation with conflict detection
- **Safe Parallel Testing**: Mohadin runs in read-only mode
- **Production Ready**: Velo Test operates in live mode
- **Container Management**: Full Portainer integration

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ (for development/validation)
- All configuration files properly set up

### Validation

Before deployment, validate the system:

```bash
python3 validate_deployment.py
```

This checks:
- Directory structure
- Required files
- Service configurations
- Docker setup
- Python imports
- Script permissions

### Deployment

Deploy all services with a single command:

```bash
./deploy.sh
```

Available deployment commands:

```bash
./deploy.sh build     # Build Docker images only
./deploy.sh start     # Start services (without rebuild) 
./deploy.sh stop      # Stop all services
./deploy.sh status    # Show service status
./deploy.sh logs      # Follow service logs
./deploy.sh help      # Show all commands
```

## Service Endpoints

After deployment, the following endpoints are available:

### Health Checks
- **Mohadin Service**: `http://localhost:8081/health`
- **Velo Test Service**: `http://localhost:8082/health`
- **WhatsApp Bridge**: `http://localhost:8080/health`

### Status Information
- **Mohadin Service**: `http://localhost:8081/status`
- **Velo Test Service**: `http://localhost:8082/status`

### Management
- **Portainer Interface**: `https://localhost:9443`

## Configuration

### Service Registry

All services are configured in `config/services.json`:

```json
{
  "services": {
    "mohadin": {
      "name": "Mohadin Group Monitor",
      "port": 8081,
      "mode": "parallel_testing",
      "status": "active"
    },
    "velo_test": {
      "name": "Velo Test Group Monitor", 
      "port": 8082,
      "mode": "production",
      "status": "active"
    }
  }
}
```

### Docker Compose

The `docker-compose.yml` defines:
- Service containers with proper health checks
- Shared network (`wa-tool-network`)
- Volume mounts for configuration and logs
- Environment variable management
- Container dependencies

## Development

### Adding New Services

1. Create service directory: `services/new_service/`
2. Implement service: `services/new_service/new_service.py`
3. Add Dockerfile: `docker/Dockerfile.new_service`
4. Update `docker-compose.yml`
5. Add to `config/services.json`
6. Run validation: `python3 validate_deployment.py`

### Service Template

All services extend `GroupService` from `services/group_service_template.py` which provides:
- Configuration management
- Logging setup
- Health check endpoints
- Graceful shutdown handling
- Environment integration

## Monitoring and Management

### Container Health

Docker health checks run every 30 seconds:
- HTTP health endpoint checks
- Service startup validation
- Automatic restart on failure

### Portainer Management

Access Portainer at `https://localhost:9443` for:
- Container status monitoring
- Log viewing
- Resource usage tracking
- Service scaling
- Stack management

### Logs

Service logs are available through:
- Docker: `docker-compose logs [service-name]`
- Portainer: Web interface log viewer
- Direct: Container volume mounts

## Safety Features

### Mohadin Service (Parallel Testing)
- ✅ Read-only monitoring of production group
- ✅ Feedback sent to monitor group only
- ✅ Separate Google Sheets tab
- ✅ Zero impact on live operations

### Velo Test Service (Production)
- ⚠️ Live monitoring and feedback
- ⚠️ Direct Google Sheets updates
- ⚠️ Production operational impact

## Troubleshooting

### Common Issues

1. **Port Conflicts**: Check `core/port_manager.py` for allocations
2. **Service Not Starting**: Check health endpoints and logs
3. **Configuration Errors**: Validate with `python3 validate_deployment.py`
4. **Docker Issues**: Ensure Docker daemon is running

### Debug Commands

```bash
# Check service status
./deploy.sh status

# View logs
./deploy.sh logs

# Check individual container
docker logs wa-tool-mohadin-service-1

# Test health endpoints
curl http://localhost:8081/health
curl http://localhost:8082/health
```

### Recovery

If services fail:

```bash
# Stop everything
./deploy.sh stop

# Rebuild and restart
./deploy.sh deploy
```

## File Structure

```
WA_Tool/
├── config/
│   └── services.json          # Service registry
├── core/
│   └── port_manager.py        # Port allocation
├── services/
│   ├── group_service_template.py
│   ├── mohadin_service/
│   │   └── mohadin_service.py
│   └── velo_test_service/
│       └── velo_test_service.py
├── docker/
│   ├── Dockerfile             # Base image
│   ├── Dockerfile.mohadin     # Mohadin specific
│   └── Dockerfile.velo_test   # Velo Test specific
├── logs/                      # Service logs
├── docker-compose.yml         # Container orchestration
├── requirements.txt           # Python dependencies
├── deploy.sh                  # Deployment script
├── validate_deployment.py     # Validation script
└── .dockerignore              # Docker ignore rules
```

## Support

For issues with:
- **Container Management**: Check Portainer interface
- **Service Configuration**: Validate with deployment validator
- **Health Checks**: Monitor service endpoints
- **Logs**: Use Docker Compose or Portainer log viewers

The microservices architecture provides better isolation, monitoring, and management capabilities compared to the previous monolithic approach.