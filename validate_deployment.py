#!/usr/bin/env python3
"""
WA_Tool Deployment Validation Script
Validates the system is ready for containerized deployment.
"""

import os
import sys
import json
from pathlib import Path

def print_header():
    print("🔍 WA_Tool Deployment Validation")
    print("=" * 50)
    print()

def check_file_exists(file_path: str, description: str) -> bool:
    """Check if a required file exists."""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ MISSING {description}: {file_path}")
        return False

def check_directory_structure() -> bool:
    """Validate the required directory structure."""
    print("📁 Checking Directory Structure:")
    
    required_dirs = [
        "config",
        "core", 
        "services",
        "services/mohadin_service",
        "services/velo_test_service",
        "docker",
        "logs"
    ]
    
    all_good = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"✅ Directory: {directory}/")
        else:
            print(f"❌ MISSING Directory: {directory}/")
            all_good = False
            
    print()
    return all_good

def check_required_files() -> bool:
    """Check for all required files."""
    print("📄 Checking Required Files:")
    
    required_files = [
        ("requirements.txt", "Python Dependencies"),
        ("docker-compose.yml", "Docker Compose Configuration"),
        (".dockerignore", "Docker Ignore File"),
        ("deploy.sh", "Deployment Script"),
        ("docker/Dockerfile", "Base Dockerfile"),
        ("docker/Dockerfile.mohadin", "Mohadin Dockerfile"),
        ("docker/Dockerfile.velo_test", "Velo Test Dockerfile"),
        ("config/services.json", "Services Configuration"),
        ("core/port_manager.py", "Port Manager"),
        ("services/group_service_template.py", "Group Service Template"),
        ("services/mohadin_service/mohadin_service.py", "Mohadin Service"),
        ("services/velo_test_service/velo_test_service.py", "Velo Test Service")
    ]
    
    all_good = True
    for file_path, description in required_files:
        if not check_file_exists(file_path, description):
            all_good = False
    
    print()
    return all_good

def validate_services_config() -> bool:
    """Validate the services configuration file."""
    print("⚙️  Validating Services Configuration:")
    
    config_file = "config/services.json"
    if not os.path.exists(config_file):
        print(f"❌ Services config file not found: {config_file}")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Check for required services
        required_services = ["mohadin", "velo_test"]
        for service in required_services:
            if service in config.get("services", {}):
                service_config = config["services"][service]
                port = service_config.get("port")
                print(f"✅ Service '{service}' configured on port {port}")
            else:
                print(f"❌ Service '{service}' not found in configuration")
                return False
                
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in services config: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading services config: {e}")
        return False
    
    print()
    return True

def check_docker_compose() -> bool:
    """Validate Docker Compose configuration."""
    print("🐳 Checking Docker Compose Configuration:")
    
    compose_file = "docker-compose.yml"
    if not os.path.exists(compose_file):
        print(f"❌ Docker Compose file not found: {compose_file}")
        return False
    
    try:
        with open(compose_file, 'r') as f:
            compose_content = f.read()
        
        # Basic validation checks
        required_services = ["mohadin-service", "velo-test-service"]
        for service in required_services:
            if service in compose_content:
                print(f"✅ Docker service '{service}' found in compose file")
            else:
                print(f"❌ Docker service '{service}' not found in compose file")
                return False
                
        # Check for required elements
        required_elements = ["networks:", "volumes:", "wa-tool-network"]
        for element in required_elements:
            if element in compose_content:
                print(f"✅ Docker element '{element}' found")
            else:
                print(f"❌ Docker element '{element}' not found")
                return False
                
    except Exception as e:
        print(f"❌ Error reading Docker Compose file: {e}")
        return False
    
    print()
    return True

def check_python_services() -> bool:
    """Check if Python services can be imported."""
    print("🐍 Checking Python Service Imports:")
    
    # Add current directory to Python path
    sys.path.insert(0, '.')
    
    try:
        # Try importing core modules
        from core.port_manager import PortManager
        print("✅ PortManager import successful")
        
        from services.group_service_template import GroupService
        print("✅ GroupService template import successful")
        
    except ImportError as e:
        print(f"❌ Python import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Python error: {e}")
        return False
    
    print()
    return True

def check_deployment_script() -> bool:
    """Check deployment script permissions."""
    print("🚀 Checking Deployment Script:")
    
    deploy_script = "deploy.sh"
    if not os.path.exists(deploy_script):
        print(f"❌ Deployment script not found: {deploy_script}")
        return False
    
    # Check if executable
    if os.access(deploy_script, os.X_OK):
        print(f"✅ Deployment script is executable")
    else:
        print(f"❌ Deployment script is not executable - run: chmod +x {deploy_script}")
        return False
    
    print()
    return True

def main():
    """Main validation function."""
    print_header()
    
    validation_checks = [
        ("Directory Structure", check_directory_structure),
        ("Required Files", check_required_files),
        ("Services Configuration", validate_services_config),
        ("Docker Compose", check_docker_compose),
        ("Python Services", check_python_services),
        ("Deployment Script", check_deployment_script)
    ]
    
    all_passed = True
    results = []
    
    for check_name, check_function in validation_checks:
        try:
            result = check_function()
            results.append((check_name, result))
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ Error in {check_name} validation: {e}")
            results.append((check_name, False))
            all_passed = False
    
    # Summary
    print("📋 VALIDATION SUMMARY")
    print("=" * 50)
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {check_name}")
    
    print()
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("✅ System is ready for containerized deployment")
        print("Run: ./deploy.sh to start the microservices")
        return 0
    else:
        print("❌ VALIDATION FAILURES DETECTED")
        print("Please fix the issues above before deploying")
        return 1

if __name__ == "__main__":
    sys.exit(main())