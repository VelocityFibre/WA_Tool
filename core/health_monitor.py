#!/usr/bin/env python3
"""
Health Monitor for WA_Tool Microservices
Monitors service health, detects failures, and provides status reporting.
"""

import json
import time
import logging
import requests
import psutil
import socket
import subprocess
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import threading
import os
import sys

class ServiceHealthMonitor:
    """
    Monitors health of WhatsApp group services.
    Provides health checks, status reporting, and failure detection.
    """
    
    def __init__(self, config_path: str = "/home/louisdup/VF/Apps/WA_Tool/config/services.json"):
        self.config_path = config_path
        self.logger = self._setup_logging()
        self.running = True
        self.check_interval = 30  # seconds
        self.health_history = {}
        self.alert_thresholds = {
            'consecutive_failures': 3,
            'response_timeout': 5,  # seconds
            'memory_limit_mb': 500,
            'cpu_limit_percent': 80
        }
        
        # Load configuration
        self.services_config = self._load_services_config()
        
        # Initialize health history for each service
        for service_id in self.services_config.get('services', {}):
            self.health_history[service_id] = {
                'last_check': None,
                'status': 'unknown',
                'consecutive_failures': 0,
                'last_failure': None,
                'uptime_start': None,
                'total_checks': 0,
                'success_count': 0
            }
            
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for health monitor."""
        logger = logging.getLogger('HealthMonitor')
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
            
    def get_process_by_port(self, port: int) -> Optional[psutil.Process]:
        """Find process using a specific port."""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'connections']):
                try:
                    if proc.info['connections']:
                        for conn in proc.info['connections']:
                            if (conn.laddr.port == port and 
                                conn.status == psutil.CONN_LISTEN):
                                return psutil.Process(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                    continue
        except Exception as e:
            self.logger.debug(f"Process lookup error for port {port}: {e}")
        return None
        
    def get_process_stats(self, process: psutil.Process) -> Dict:
        """Get detailed process statistics."""
        try:
            with process.oneshot():
                return {
                    'pid': process.pid,
                    'name': process.name(),
                    'status': process.status(),
                    'cpu_percent': process.cpu_percent(interval=0.1),
                    'memory_mb': process.memory_info().rss / 1024 / 1024,
                    'memory_percent': process.memory_percent(),
                    'create_time': datetime.fromtimestamp(process.create_time()),
                    'num_threads': process.num_threads(),
                    'cmdline': ' '.join(process.cmdline()[:3])  # First 3 args only
                }
        except Exception as e:
            self.logger.debug(f"Process stats error: {e}")
            return {}
            
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
            if self.is_port_open(host, port, timeout=self.alert_thresholds['response_timeout']):
                health_status['status'] = 'healthy'
                health_status['details']['port_open'] = True
                
                # Try to get process info
                process = self.get_process_by_port(port)
                if process:
                    stats = self.get_process_stats(process)
                    health_status['details']['process'] = stats
                    
                    # Check resource usage
                    if stats.get('memory_mb', 0) > self.alert_thresholds['memory_limit_mb']:
                        health_status['warnings'] = health_status.get('warnings', [])
                        health_status['warnings'].append(f"High memory usage: {stats['memory_mb']:.1f}MB")
                        
                    if stats.get('cpu_percent', 0) > self.alert_thresholds['cpu_limit_percent']:
                        health_status['warnings'] = health_status.get('warnings', [])
                        health_status['warnings'].append(f"High CPU usage: {stats['cpu_percent']:.1f}%")
                        
                # Try health endpoint if available
                try:
                    health_url = f"http://{host}:{port}/health"
                    response = requests.get(health_url, timeout=self.alert_thresholds['response_timeout'])
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
            if self.is_port_open('localhost', port, timeout=self.alert_thresholds['response_timeout']):
                health_status['status'] = 'healthy'
                health_status['details']['port_open'] = True
                
                # Get process information
                process = self.get_process_by_port(port)
                if process:
                    stats = self.get_process_stats(process)
                    health_status['details']['process'] = stats
                    
                    # Calculate uptime
                    if stats.get('create_time'):
                        uptime = datetime.now() - stats['create_time']
                        health_status['details']['uptime_seconds'] = uptime.total_seconds()
                        health_status['details']['uptime_readable'] = str(uptime).split('.')[0]
                        
                    # Resource usage checks
                    memory_mb = stats.get('memory_mb', 0)
                    cpu_percent = stats.get('cpu_percent', 0)
                    
                    if memory_mb > self.alert_thresholds['memory_limit_mb']:
                        health_status['warnings'].append(f"High memory usage: {memory_mb:.1f}MB")
                        
                    if cpu_percent > self.alert_thresholds['cpu_limit_percent']:
                        health_status['warnings'].append(f"High CPU usage: {cpu_percent:.1f}%")
                        
                    # Check if process name matches service
                    process_name = stats.get('name', '').lower()
                    if service_id.lower() not in process_name and 'python' not in process_name:
                        health_status['warnings'].append(f"Process name mismatch: {process_name}")
                        
                else:
                    health_status['warnings'].append("Port open but process not found")
                    
            else:
                health_status['details']['port_open'] = False
                health_status['details']['error'] = f'Port {port} not responding'
                
                # Check if there are any processes that might be the service
                service_processes = self._find_service_processes(service_id)
                if service_processes:
                    health_status['details']['orphaned_processes'] = service_processes
                    health_status['warnings'].append(f"Found {len(service_processes)} potential service processes not on expected port")
                    
        except Exception as e:
            health_status['details']['error'] = str(e)
            
        return health_status
        
    def _find_service_processes(self, service_id: str) -> List[Dict]:
        """Find processes that might belong to a service."""
        processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline']).lower()
                    if service_id.lower() in cmdline and 'python' in cmdline:
                        processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline[:100]  # Truncate long command lines
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            self.logger.debug(f"Service process search error: {e}")
        return processes
        
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
            
            # Update history
            history = self.health_history[service_id]
            history['last_check'] = datetime.now()
            history['total_checks'] += 1
            
            if service_health['status'] == 'healthy':
                health_report['summary']['healthy_services'] += 1
                history['success_count'] += 1
                history['consecutive_failures'] = 0
                
                # Set uptime start if not set
                if not history['uptime_start']:
                    history['uptime_start'] = datetime.now()
                    
            else:
                health_report['summary']['unhealthy_services'] += 1
                history['consecutive_failures'] += 1
                history['last_failure'] = datetime.now()
                history['uptime_start'] = None
                health_report['overall_status'] = 'unhealthy'
                
            if service_health.get('warnings'):
                health_report['summary']['services_with_warnings'] += 1
                
            # Update service status in history
            history['status'] = service_health['status']
            
        return health_report
        
    def get_service_alerts(self, health_report: Dict) -> List[Dict]:
        """Generate alerts based on health report."""
        alerts = []
        
        # Bridge alerts
        bridge_health = health_report.get('whatsapp_bridge', {})
        if bridge_health.get('status') != 'healthy':
            alerts.append({
                'type': 'critical',
                'service': 'whatsapp_bridge',
                'message': 'WhatsApp Bridge is unhealthy',
                'details': bridge_health.get('details', {})
            })
            
        # Service alerts
        for service_id, service_health in health_report.get('services', {}).items():
            history = self.health_history[service_id]
            
            # Consecutive failure alert
            if history['consecutive_failures'] >= self.alert_thresholds['consecutive_failures']:
                alerts.append({
                    'type': 'critical',
                    'service': service_id,
                    'message': f"Service has failed {history['consecutive_failures']} consecutive times",
                    'details': service_health.get('details', {})
                })
                
            # Resource usage alerts
            if service_health.get('warnings'):
                alerts.append({
                    'type': 'warning',
                    'service': service_id,
                    'message': 'Resource usage warnings',
                    'details': {'warnings': service_health['warnings']}
                })
                
        return alerts
        
    def print_health_summary(self, health_report: Dict):
        """Print a formatted health summary."""
        timestamp = datetime.fromisoformat(health_report['timestamp'].replace('Z', '+00:00'))
        summary = health_report['summary']
        
        print(f"\n🏥 HEALTH MONITOR REPORT - {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Overall status
        status_emoji = "✅" if health_report['overall_status'] == 'healthy' else "❌" if health_report['overall_status'] == 'unhealthy' else "⚠️"
        print(f"Overall Status: {status_emoji} {health_report['overall_status'].upper()}")
        print()
        
        # WhatsApp Bridge
        bridge = health_report.get('whatsapp_bridge', {})
        bridge_emoji = "✅" if bridge.get('status') == 'healthy' else "❌"
        print(f"WhatsApp Bridge: {bridge_emoji} {bridge.get('status', 'unknown').upper()}")
        if bridge.get('details', {}).get('process'):
            proc = bridge['details']['process']
            print(f"  PID: {proc.get('pid')}, Memory: {proc.get('memory_mb', 0):.1f}MB, CPU: {proc.get('cpu_percent', 0):.1f}%")
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
                uptime = service_health['details'].get('uptime_readable', 'unknown')
                print(f"      PID: {proc.get('pid')}, Uptime: {uptime}")
                print(f"      Memory: {proc.get('memory_mb', 0):.1f}MB, CPU: {proc.get('cpu_percent', 0):.1f}%")
                
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
        self.logger.info("🏥 Starting Health Monitor...")
        self.logger.info(f"⏰ Check interval: {self.check_interval} seconds")
        self.logger.info(f"👀 Monitoring services: {list(self.services_config.get('services', {}).keys())}")
        
        try:
            while self.running:
                try:
                    # Run health checks
                    health_report = self.run_health_checks()
                    
                    # Print summary
                    self.print_health_summary(health_report)
                    
                    # Check for alerts
                    alerts = self.get_service_alerts(health_report)
                    if alerts:
                        self.logger.warning(f"🚨 {len(alerts)} alerts generated")
                        for alert in alerts:
                            level = logging.CRITICAL if alert['type'] == 'critical' else logging.WARNING
                            self.logger.log(level, f"ALERT: {alert['service']} - {alert['message']}")
                            
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
    
    parser = argparse.ArgumentParser(description='WA_Tool Health Monitor')
    parser.add_argument('--config', help='Path to services.json configuration')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
    parser.add_argument('--once', action='store_true', help='Run health check once and exit')
    
    args = parser.parse_args()
    
    monitor = ServiceHealthMonitor(args.config or "/home/louisdup/VF/Apps/WA_Tool/config/services.json")
    monitor.check_interval = args.interval
    
    if args.once:
        print("🏥 Running one-time health check...")
        health_report = monitor.run_health_checks()
        monitor.print_health_summary(health_report)
        alerts = monitor.get_service_alerts(health_report)
        if alerts:
            print(f"\n🚨 {len(alerts)} alerts:")
            for alert in alerts:
                print(f"  {alert['type'].upper()}: {alert['service']} - {alert['message']}")
    else:
        monitor.start_monitoring()

if __name__ == "__main__":
    main()