#!/usr/bin/env python3
"""
Simple Health Monitor for WA_Tool Microservices
Basic health monitoring using only standard Python libraries + requests.
"""

import json
import time
import logging
import requests
import socket
import subprocess
import signal
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

class SimpleHealthMonitor:
    """
    Simple health monitor using only standard libraries.
    Checks port availability and basic service health.
    """
    
    def __init__(self, config_path: str = "/home/louisdup/VF/Apps/WA_Tool/config/services.json"):
        self.config_path = config_path
        self.logger = self._setup_logging()
        self.running = True
        self.check_interval = 30  # seconds
        
        # Load configuration
        self.services_config = self._load_services_config()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging."""
        logger = logging.getLogger('SimpleHealthMonitor')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            log_dir = "/home/louisdup/VF/Apps/WA_Tool/logs"
            os.makedirs(log_dir, exist_ok=True)
            file_handler = logging.FileHandler(f"{log_dir}/health_monitor.log")
            file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        return logger
        
    def _load_services_config(self) -> Dict:
        """Load services configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"❌ Failed to load services config: {e}")
            return {'services': {}}
            
    def _signal_handler(self, signum, frame):
        """Handle graceful shutdown."""
        self.logger.info(f"📡 Received signal {signum}. Shutting down health monitor...")
        self.running = False
        
    def is_port_open(self, host: str, port: int, timeout: int = 5) -> bool:
        """Check if a port is open and responding."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(timeout)
                result = sock.connect_ex((host, port))
                return result == 0
        except Exception as e:
            self.logger.debug(f"Port check error for {host}:{port} - {e}")
            return False
            
    def get_process_on_port(self, port: int) -> Optional[Dict]:
        """Find process using a port using lsof command."""
        try:
            result = subprocess.run(
                ['lsof', '-i', f':{port}', '-t'], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip().split('\n')[0]
                
                # Get process info
                try:
                    ps_result = subprocess.run(
                        ['ps', '-p', pid, '-o', 'pid,ppid,comm,%cpu,%mem,etime'],
                        capture_output=True, text=True, timeout=5
                    )
                    if ps_result.returncode == 0:
                        lines = ps_result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            parts = lines[1].split()
                            return {
                                'pid': int(parts[0]),
                                'ppid': int(parts[1]),
                                'name': parts[2],
                                'cpu_percent': float(parts[3]) if parts[3] != '-' else 0.0,
                                'memory_percent': float(parts[4]) if parts[4] != '-' else 0.0,
                                'uptime': parts[5] if len(parts) > 5 else 'unknown'
                            }
                except (subprocess.TimeoutExpired, ValueError, IndexError):
                    return {'pid': int(pid), 'name': 'unknown'}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
        
    def check_whatsapp_bridge_health(self) -> Dict:
        """Check WhatsApp bridge health."""
        bridge_config = self.services_config.get('global_configuration', {}).get('whatsapp_bridge', {})
        host = bridge_config.get('host', 'localhost')
        port = bridge_config.get('port', 8080)
        
        health_status = {
            'service': 'whatsapp_bridge',
            'status': 'unhealthy',
            'host': host,
            'port': port,
            'timestamp': datetime.now().isoformat(),
            'details': {}
        }
        
        try:
            # Check if port is open
            if self.is_port_open(host, port, timeout=5):
                health_status['status'] = 'healthy'
                health_status['details']['port_open'] = True
                
                # Try to get process info
                process_info = self.get_process_on_port(port)
                if process_info:
                    health_status['details']['process'] = process_info
                    
                # Try health endpoint if available
                try:
                    health_url = f"http://{host}:{port}/health"
                    response = requests.get(health_url, timeout=5)
                    health_status['details']['http_health'] = {
                        'status_code': response.status_code,
                        'response_time_ms': response.elapsed.total_seconds() * 1000,
                        'available': response.status_code == 200
                    }
                except requests.exceptions.RequestException as e:
                    health_status['details']['http_health'] = {
                        'available': False,
                        'error': str(e)
                    }
            else:
                health_status['details']['port_open'] = False
                health_status['details']['error'] = 'Port not responding'
                
        except Exception as e:
            health_status['details']['error'] = str(e)
            
        return health_status
        
    def check_service_health(self, service_id: str, service_config: Dict) -> Dict:
        """Check health of a specific service."""
        port = service_config.get('port')
        
        health_status = {
            'service_id': service_id,
            'service_name': service_config.get('display_name', service_id),
            'status': 'unhealthy',
            'port': port,
            'timestamp': datetime.now().isoformat(),
            'details': {},
            'warnings': []
        }
        
        if not port:
            health_status['details']['error'] = 'No port configured'
            return health_status
            
        try:
            # Check if service port is open
            if self.is_port_open('localhost', port, timeout=5):
                health_status['status'] = 'healthy'
                health_status['details']['port_open'] = True
                
                # Get process information
                process_info = self.get_process_on_port(port)
                if process_info:
                    health_status['details']['process'] = process_info
                    
                    # Simple resource checks
                    cpu_percent = process_info.get('cpu_percent', 0)
                    memory_percent = process_info.get('memory_percent', 0)
                    
                    if cpu_percent > 80:
                        health_status['warnings'].append(f"High CPU usage: {cpu_percent:.1f}%")
                        
                    if memory_percent > 10:  # More than 10% system memory
                        health_status['warnings'].append(f"High memory usage: {memory_percent:.1f}%")
                        
                else:
                    health_status['warnings'].append("Port open but process info unavailable")
                    
            else:
                health_status['details']['port_open'] = False
                health_status['details']['error'] = f'Port {port} not responding'
                
        except Exception as e:
            health_status['details']['error'] = str(e)
            
        return health_status
        
    def run_health_checks(self) -> Dict:
        """Run health checks for all services."""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'services': {},
            'whatsapp_bridge': {},
            'summary': {
                'total_services': 0,
                'healthy_services': 0,
                'unhealthy_services': 0,
                'services_with_warnings': 0
            }
        }
        
        # Check WhatsApp bridge
        bridge_health = self.check_whatsapp_bridge_health()
        health_report['whatsapp_bridge'] = bridge_health
        
        if bridge_health['status'] != 'healthy':
            health_report['overall_status'] = 'degraded'
            
        # Check each service
        services = self.services_config.get('services', {})
        health_report['summary']['total_services'] = len(services)
        
        for service_id, service_config in services.items():
            service_health = self.check_service_health(service_id, service_config)
            health_report['services'][service_id] = service_health
            
            if service_health['status'] == 'healthy':
                health_report['summary']['healthy_services'] += 1
            else:
                health_report['summary']['unhealthy_services'] += 1
                health_report['overall_status'] = 'unhealthy'
                
            if service_health.get('warnings'):
                health_report['summary']['services_with_warnings'] += 1
                
        return health_report
        
    def print_health_summary(self, health_report: Dict):
        """Print a formatted health summary."""
        timestamp = datetime.fromisoformat(health_report['timestamp'])
        summary = health_report['summary']
        
        print(f"\\n🏥 HEALTH MONITOR REPORT - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Overall status
        status_emoji = "✅" if health_report['overall_status'] == 'healthy' else "❌" if health_report['overall_status'] == 'unhealthy' else "⚠️"
        print(f"Overall Status: {status_emoji} {health_report['overall_status'].upper()}")
        print()
        
        # WhatsApp Bridge
        bridge = health_report.get('whatsapp_bridge', {})
        bridge_emoji = "✅" if bridge.get('status') == 'healthy' else "❌"
        print(f"WhatsApp Bridge: {bridge_emoji} {bridge.get('status', 'unknown').upper()} (:{bridge.get('port', 'N/A')})")
        if bridge.get('details', {}).get('process'):
            proc = bridge['details']['process']
            print(f"  PID: {proc.get('pid')}, Uptime: {proc.get('uptime', 'unknown')}")
        print()
        
        # Services summary
        print(f"Services: {summary['healthy_services']}/{summary['total_services']} healthy")
        if summary['services_with_warnings'] > 0:
            print(f"Warnings: {summary['services_with_warnings']} services have warnings")
        print()
        
        # Individual services
        print("Service Details:")
        for service_id, service_health in health_report.get('services', {}).items():
            status = service_health.get('status', 'unknown')
            emoji = "✅" if status == 'healthy' else "❌"
            port = service_health.get('port', 'N/A')
            
            print(f"  {emoji} {service_health.get('service_name', service_id)} (:{port}) - {status.upper()}")
            
            # Process details
            if service_health.get('details', {}).get('process'):
                proc = service_health['details']['process']
                print(f"      PID: {proc.get('pid')}, Uptime: {proc.get('uptime', 'unknown')}")
                print(f"      CPU: {proc.get('cpu_percent', 0):.1f}%, Memory: {proc.get('memory_percent', 0):.1f}%")
                
            # Warnings
            if service_health.get('warnings'):
                for warning in service_health['warnings']:
                    print(f"      ⚠️  {warning}")
                    
            # Errors
            if service_health.get('details', {}).get('error'):
                print(f"      ❌ {service_health['details']['error']}")
                
        print()
        
    def start_monitoring(self):
        """Start the health monitoring loop."""
        self.logger.info("🏥 Starting Simple Health Monitor...")
        self.logger.info(f"⏰ Check interval: {self.check_interval} seconds")
        self.logger.info(f"👀 Monitoring services: {list(self.services_config.get('services', {}).keys())}")
        
        try:
            while self.running:
                try:
                    # Run health checks
                    health_report = self.run_health_checks()
                    
                    # Print summary
                    self.print_health_summary(health_report)
                    
                    # Wait for next check
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("🛑 Keyboard interrupt received")
                    break
                except Exception as e:
                    self.logger.error(f"❌ Health check error: {e}")
                    time.sleep(self.check_interval)
                    
        except Exception as e:
            self.logger.error(f"❌ Fatal health monitor error: {e}")
        finally:
            self.logger.info("🛑 Health Monitor stopped")
            
def main():
    """Main entry point for health monitor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='WA_Tool Simple Health Monitor')
    parser.add_argument('--config', help='Path to services.json configuration')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run health check once and exit')
    
    args = parser.parse_args()
    
    monitor = SimpleHealthMonitor(args.config or "/home/louisdup/VF/Apps/WA_Tool/config/services.json")
    monitor.check_interval = args.interval
    
    if args.once:
        print("🏥 Running one-time health check...")
        health_report = monitor.run_health_checks()
        monitor.print_health_summary(health_report)
    else:
        monitor.start_monitoring()

if __name__ == "__main__":
    main()