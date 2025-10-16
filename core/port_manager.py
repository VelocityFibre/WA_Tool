#!/usr/bin/env python3
"""
Port Manager for WA_Tool Microservices
Handles automatic port allocation, conflict detection, and port availability checking.
"""

import json
import socket
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import os

class PortManager:
    """
    Manages port allocation for WhatsApp group services.
    Ensures no conflicts and provides automatic port assignment.
    """
    
    def __init__(self, config_path: str = "/home/louisdup/VF/Apps/WA_Tool/config/services.json"):
        self.config_path = config_path
        self.logger = self._setup_logging()
        self.base_port = 8080
        self.reserved_ports = [8080]  # Dashboard and WhatsApp bridge
        self.max_port = 8099  # Stay within reasonable range
        
        # Load existing configuration
        self.config = self._load_config()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for port manager."""
        logger = logging.getLogger('PortManager')
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
        
    def _load_config(self) -> Dict:
        """Load configuration from services.json."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.logger.info(f"✅ Loaded configuration from {self.config_path}")
                return config
        except FileNotFoundError:
            self.logger.error(f"❌ Configuration file not found: {self.config_path}")
            return self._create_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"❌ Invalid JSON in config file: {e}")
            return self._create_default_config()
            
    def _create_default_config(self) -> Dict:
        """Create default configuration if none exists."""
        default_config = {
            "port_allocation": {
                "base_port": 8080,
                "management_dashboard": 8080,
                "whatsapp_bridge": 8080,
                "next_available_port": 8081,
                "reserved_ports": [8080],
                "allocated_ports": {}
            },
            "services": {}
        }
        self.logger.info("📝 Created default configuration")
        return default_config
        
    def _save_config(self) -> bool:
        """Save configuration back to file."""
        try:
            # Update timestamp
            if "port_allocation" in self.config:
                self.config["port_allocation"]["last_updated"] = datetime.now().isoformat()
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info(f"💾 Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to save configuration: {e}")
            return False
            
    def is_port_available(self, port: int, host: str = "localhost") -> bool:
        """
        Check if a port is available for binding.
        
        Args:
            port: Port number to check
            host: Host to check (default: localhost)
            
        Returns:
            True if port is available, False otherwise
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                is_available = result != 0  # 0 means port is in use
                
                if is_available:
                    self.logger.debug(f"✅ Port {port} is available")
                else:
                    self.logger.debug(f"❌ Port {port} is in use")
                    
                return is_available
        except Exception as e:
            self.logger.error(f"❌ Error checking port {port}: {e}")
            return False
            
    def get_allocated_ports(self) -> Dict[str, str]:
        """Get currently allocated ports."""
        return self.config.get("port_allocation", {}).get("allocated_ports", {})
        
    def get_next_available_port(self) -> int:
        """
        Find the next available port starting from base_port + 1.
        
        Returns:
            Next available port number
        """
        allocated_ports = self.get_allocated_ports()
        used_ports = set(int(port) for port in allocated_ports.keys())
        used_ports.update(self.reserved_ports)
        
        # Start from base_port + 1
        for port in range(self.base_port + 1, self.max_port + 1):
            if port not in used_ports and self.is_port_available(port):
                self.logger.info(f"🔍 Next available port: {port}")
                return port
                
        raise Exception(f"No available ports in range {self.base_port + 1}-{self.max_port}")
        
    def allocate_port(self, service_id: str, preferred_port: Optional[int] = None) -> int:
        """
        Allocate a port for a service.
        
        Args:
            service_id: Unique service identifier
            preferred_port: Preferred port number (optional)
            
        Returns:
            Allocated port number
        """
        allocated_ports = self.get_allocated_ports()
        
        # Check if service already has a port
        for port_str, existing_service_id in allocated_ports.items():
            if existing_service_id == service_id:
                port = int(port_str)
                self.logger.info(f"🔄 Service '{service_id}' already has port {port}")
                return port
                
        # Try preferred port if specified
        if preferred_port is not None:
            if self._can_allocate_port(preferred_port, service_id):
                return self._assign_port(service_id, preferred_port)
            else:
                self.logger.warning(f"⚠️  Preferred port {preferred_port} not available for '{service_id}'")
                
        # Find next available port
        port = self.get_next_available_port()
        return self._assign_port(service_id, port)
        
    def _can_allocate_port(self, port: int, service_id: str) -> bool:
        """Check if a specific port can be allocated."""
        if port in self.reserved_ports:
            self.logger.debug(f"❌ Port {port} is reserved")
            return False
            
        allocated_ports = self.get_allocated_ports()
        if str(port) in allocated_ports:
            existing_service = allocated_ports[str(port)]
            if existing_service != service_id:
                self.logger.debug(f"❌ Port {port} already allocated to '{existing_service}'")
                return False
                
        return self.is_port_available(port)
        
    def _assign_port(self, service_id: str, port: int) -> int:
        """Assign a port to a service and update configuration."""
        allocated_ports = self.get_allocated_ports()
        allocated_ports[str(port)] = service_id
        
        # Update configuration
        if "port_allocation" not in self.config:
            self.config["port_allocation"] = {}
        self.config["port_allocation"]["allocated_ports"] = allocated_ports
        self.config["port_allocation"]["next_available_port"] = port + 1
        
        # Update service configuration if exists
        if "services" in self.config and service_id in self.config["services"]:
            self.config["services"][service_id]["port"] = port
            self.config["services"][service_id]["last_updated"] = datetime.now().isoformat()
            
        self._save_config()
        self.logger.info(f"✅ Allocated port {port} to service '{service_id}'")
        return port
        
    def deallocate_port(self, service_id: str) -> bool:
        """
        Deallocate port from a service.
        
        Args:
            service_id: Service identifier
            
        Returns:
            True if successfully deallocated
        """
        allocated_ports = self.get_allocated_ports()
        
        # Find port for service
        port_to_remove = None
        for port_str, existing_service_id in allocated_ports.items():
            if existing_service_id == service_id:
                port_to_remove = port_str
                break
                
        if port_to_remove:
            del allocated_ports[port_to_remove]
            self.config["port_allocation"]["allocated_ports"] = allocated_ports
            
            # Update service configuration
            if "services" in self.config and service_id in self.config["services"]:
                self.config["services"][service_id]["port"] = None
                self.config["services"][service_id]["status"] = "port_deallocated"
                self.config["services"][service_id]["last_updated"] = datetime.now().isoformat()
                
            self._save_config()
            self.logger.info(f"🗑️  Deallocated port {port_to_remove} from service '{service_id}'")
            return True
        else:
            self.logger.warning(f"⚠️  No port found for service '{service_id}'")
            return False
            
    def get_service_port(self, service_id: str) -> Optional[int]:
        """Get port number for a specific service."""
        allocated_ports = self.get_allocated_ports()
        for port_str, existing_service_id in allocated_ports.items():
            if existing_service_id == service_id:
                return int(port_str)
        return None
        
    def validate_port_allocation(self) -> Dict[str, List[str]]:
        """
        Validate current port allocations and detect conflicts.
        
        Returns:
            Dictionary with 'errors' and 'warnings' lists
        """
        errors = []
        warnings = []
        
        allocated_ports = self.get_allocated_ports()
        
        # Check for duplicate allocations
        service_counts = {}
        for port_str, service_id in allocated_ports.items():
            if service_id in service_counts:
                service_counts[service_id].append(port_str)
            else:
                service_counts[service_id] = [port_str]
                
        for service_id, ports in service_counts.items():
            if len(ports) > 1:
                errors.append(f"Service '{service_id}' allocated to multiple ports: {ports}")
                
        # Check if allocated ports are actually available
        for port_str, service_id in allocated_ports.items():
            port = int(port_str)
            if not self.is_port_available(port):
                warnings.append(f"Port {port} allocated to '{service_id}' but appears to be in use")
                
        # Check for reserved port conflicts
        for port_str in allocated_ports.keys():
            port = int(port_str)
            if port in self.reserved_ports:
                errors.append(f"Port {port} is reserved but allocated to service")
                
        return {"errors": errors, "warnings": warnings}
        
    def get_port_status_summary(self) -> Dict:
        """Get a summary of port allocation status."""
        allocated_ports = self.get_allocated_ports()
        validation = self.validate_port_allocation()
        
        return {
            "total_allocated": len(allocated_ports),
            "allocated_ports": allocated_ports,
            "reserved_ports": self.reserved_ports,
            "next_available": self.get_next_available_port(),
            "port_range": f"{self.base_port + 1}-{self.max_port}",
            "validation_errors": len(validation["errors"]),
            "validation_warnings": len(validation["warnings"]),
            "validation": validation
        }
        
def main():
    """Test the port manager functionality."""
    print("🧪 Testing Port Manager...")
    
    port_manager = PortManager()
    
    # Test port allocation
    print("\n1. Testing port allocation:")
    mohadin_port = port_manager.allocate_port("mohadin", preferred_port=8081)
    print(f"   Mohadin allocated to port: {mohadin_port}")
    
    velo_port = port_manager.allocate_port("velo_test", preferred_port=8082)
    print(f"   Velo Test allocated to port: {velo_port}")
    
    # Test port status
    print("\n2. Port status summary:")
    status = port_manager.get_port_status_summary()
    print(f"   Total allocated ports: {status['total_allocated']}")
    print(f"   Allocated ports: {status['allocated_ports']}")
    print(f"   Next available port: {status['next_available']}")
    
    # Test validation
    print("\n3. Validation results:")
    validation = port_manager.validate_port_allocation()
    print(f"   Errors: {len(validation['errors'])}")
    print(f"   Warnings: {len(validation['warnings'])}")
    
    if validation['errors']:
        print("   Errors:", validation['errors'])
    if validation['warnings']:
        print("   Warnings:", validation['warnings'])
        
    print("\n✅ Port Manager test complete!")

if __name__ == "__main__":
    main()