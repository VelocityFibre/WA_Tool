#!/bin/bash

# WA_Tool Microservices Deployment Script
# This script builds and deploys the WhatsApp monitoring microservices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="wa-tool"
COMPOSE_FILE="docker-compose.yml"

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  WA_Tool Microservices Deployment${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    if [ ! -f "$COMPOSE_FILE" ]; then
        print_error "docker-compose.yml not found in current directory"
        exit 1
    fi
    
    print_status "Prerequisites check passed"
}

build_services() {
    print_status "Building Docker images..."
    
    # Build images with no cache to ensure latest changes
    docker-compose build --no-cache
    
    if [ $? -eq 0 ]; then
        print_status "All services built successfully"
    else
        print_error "Failed to build services"
        exit 1
    fi
}

start_services() {
    print_status "Starting services..."
    
    # Stop any running services first
    docker-compose down
    
    # Start services in detached mode
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        print_status "All services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
}

show_status() {
    print_status "Service Status:"
    echo
    docker-compose ps
    echo
    
    print_status "Service Logs (last 10 lines):"
    echo
    docker-compose logs --tail=10
}

show_endpoints() {
    echo
    print_status "Service Endpoints:"
    echo -e "  ${BLUE}WhatsApp Bridge:${NC}     http://localhost:8080"
    echo -e "  ${BLUE}Mohadin Service:${NC}     http://localhost:8081"
    echo -e "  ${BLUE}Velo Test Service:${NC}   http://localhost:8082"
    echo -e "  ${BLUE}Portainer:${NC}           https://localhost:9443"
    echo
}

main() {
    print_header
    
    # Parse command line arguments
    case "${1:-deploy}" in
        "build")
            check_prerequisites
            build_services
            ;;
        "start")
            check_prerequisites
            start_services
            show_status
            show_endpoints
            ;;
        "stop")
            print_status "Stopping services..."
            docker-compose down
            ;;
        "status")
            show_status
            ;;
        "logs")
            docker-compose logs -f
            ;;
        "deploy"|"")
            check_prerequisites
            build_services
            start_services
            show_status
            show_endpoints
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [COMMAND]"
            echo
            echo "Commands:"
            echo "  deploy    Build and start all services (default)"
            echo "  build     Build Docker images only"
            echo "  start     Start services (without rebuild)"
            echo "  stop      Stop all services"
            echo "  status    Show service status"
            echo "  logs      Follow service logs"
            echo "  help      Show this help message"
            ;;
        *)
            print_error "Unknown command: $1"
            print_warning "Use '$0 help' to see available commands"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"