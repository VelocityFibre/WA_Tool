#!/usr/bin/env python3
"""
COMPREHENSIVE SYSTEM HEALTH CHECKER
===================================

This script provides REAL status checks, not just "container running" status.
It validates actual functionality of each service.

"""
import subprocess
import json
import sqlite3
import time
import requests
from datetime import datetime, timedelta
import os

def run_cmd(cmd):
    """Run command and return result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_container_status():
    """Check Docker container status"""
    print("🐳 DOCKER CONTAINER STATUS:")
    success, stdout, stderr = run_cmd("docker ps --format '{{.Names}}\t{{.Status}}'")
    if success:
        lines = stdout.split('\n')
        containers = {}
        for line in lines:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    name = parts[0].strip()
                    status = parts[1].strip()
                    containers[name] = status
        
        required_containers = ['wa-bridge-privacy', 'wa-drop-monitor', 'wa-qa-monitor']
        all_running = True
        
        for container in required_containers:
            if container in containers:
                if 'Up' in containers[container]:
                    print(f"  ✅ {container}: {containers[container]}")
                else:
                    print(f"  ❌ {container}: {containers[container]}")
                    all_running = False
            else:
                print(f"  ❌ {container}: NOT FOUND")
                all_running = False
        
        return all_running, containers
    else:
        print(f"  ❌ Docker command failed: {stderr}")
        return False, {}

def check_whatsapp_bridge():
    """Check WhatsApp Bridge actual functionality"""
    print("\n📱 WHATSAPP BRIDGE FUNCTIONALITY:")
    
    # 1. Check if API is responding
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        print(f"  ✅ API responding: {response.status_code}")
        api_ok = True
    except Exception as e:
        print(f"  ❌ API not responding: {e}")
        api_ok = False
    
    # 2. Check if WhatsApp is connected (from logs)
    success, stdout, stderr = run_cmd("docker logs wa-bridge-privacy --tail=10")
    if success:
        recent_logs = stdout
        if "Connected to WhatsApp" in recent_logs:
            last_connected = [line for line in recent_logs.split('\n') if "Connected to WhatsApp" in line]
            if last_connected:
                print(f"  ✅ WhatsApp Connected: {last_connected[-1]}")
                wa_connected = True
            else:
                wa_connected = False
        else:
            print(f"  ❌ WhatsApp not connected in recent logs")
            wa_connected = False
            
        # Check for recent errors
        if "ERROR" in recent_logs:
            errors = [line for line in recent_logs.split('\n') if "ERROR" in line]
            print(f"  ⚠️  Recent errors: {len(errors)} found")
            for error in errors[-3:]:  # Show last 3 errors
                print(f"    {error}")
    else:
        print(f"  ❌ Cannot read bridge logs: {stderr}")
        wa_connected = False
    
    # 3. Check if messages are being stored
    try:
        conn = sqlite3.connect('docker-data/whatsapp-sessions/messages.db')
        cursor = conn.cursor()
        
        # Check recent messages (last hour)
        one_hour_ago = time.time() - 3600
        cursor.execute("""
            SELECT COUNT(*) FROM messages 
            WHERE timestamp > ? AND chat_jid = '120363421664266245@g.us'
        """, (one_hour_ago,))
        
        recent_count = cursor.fetchone()[0]
        print(f"  📊 Messages stored (last hour): {recent_count}")
        
        # Check latest message
        cursor.execute("""
            SELECT content, datetime(timestamp, 'unixepoch', 'localtime') 
            FROM messages 
            WHERE chat_jid = '120363421664266245@g.us' 
            ORDER BY timestamp DESC LIMIT 1
        """)
        
        latest = cursor.fetchone()
        if latest:
            print(f"  📝 Latest message: '{latest[0]}' at {latest[1]}")
            storage_ok = True
        else:
            print(f"  ❌ No messages found in database")
            storage_ok = False
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"  ❌ Database check failed: {e}")
        storage_ok = False
    
    bridge_health = api_ok and wa_connected and storage_ok
    return bridge_health, {"api": api_ok, "whatsapp": wa_connected, "storage": storage_ok}

def check_drop_monitor():
    """Check Drop Monitor functionality"""
    print("\n📊 DROP MONITOR FUNCTIONALITY:")
    
    # Check if container is processing
    success, stdout, stderr = run_cmd("docker logs wa-drop-monitor --tail=20")
    if success:
        logs = stdout
        
        # Look for recent activity
        if "INFO" in logs:
            recent_activity = [line for line in logs.split('\n') if "INFO" in line and "2025-10-02" in line]
            if recent_activity:
                print(f"  ✅ Recent activity: {len(recent_activity)} log entries")
                print(f"    Latest: {recent_activity[-1]}")
            else:
                print(f"  ⚠️  No recent activity in logs")
        
        # Check for errors
        if "ERROR" in logs:
            errors = [line for line in logs.split('\n') if "ERROR" in line]
            print(f"  ❌ Errors found: {len(errors)}")
            for error in errors[-2:]:
                print(f"    {error}")
            monitor_ok = False
        else:
            print(f"  ✅ No errors in recent logs")
            monitor_ok = True
            
        # Check if it's actually monitoring
        if "Checking for new messages" in logs or "Found" in logs:
            print(f"  ✅ Actively monitoring messages")
            actively_monitoring = True
        else:
            print(f"  ⚠️  No clear monitoring activity visible")
            actively_monitoring = False
            
    else:
        print(f"  ❌ Cannot read monitor logs: {stderr}")
        monitor_ok = False
        actively_monitoring = False
    
    return monitor_ok and actively_monitoring, {"logs_ok": monitor_ok, "monitoring": actively_monitoring}

def check_google_sheets():
    """Check Google Sheets access"""
    print("\n📊 GOOGLE SHEETS ACCESS:")
    
    # Check QA monitor logs for Google Sheets connectivity
    success, stdout, stderr = run_cmd("docker logs wa-qa-monitor --tail=10")
    if success:
        logs = stdout
        
        if "Google Sheets connection OK" in logs:
            print(f"  ✅ Google Sheets API connected")
            sheets_ok = True
        elif "403" in logs or "SERVICE_DISABLED" in logs:
            print(f"  ❌ Google Sheets API disabled or permission denied")
            sheets_ok = False
        elif "ERROR" in logs:
            errors = [line for line in logs.split('\n') if "ERROR" in line]
            print(f"  ❌ Google Sheets errors: {len(errors)}")
            for error in errors[-2:]:
                print(f"    {error[:100]}...")
            sheets_ok = False
        else:
            print(f"  ⚠️  Google Sheets status unclear from logs")
            sheets_ok = False
    else:
        print(f"  ❌ Cannot read QA monitor logs: {stderr}")
        sheets_ok = False
    
    return sheets_ok

def check_kill_switch():
    """Check Kill Switch"""
    print("\n🚨 KILL SWITCH STATUS:")
    
    success, stdout, stderr = run_cmd("ps aux | grep kill_switch.py | grep -v grep")
    if success and stdout.strip():
        print(f"  ✅ Kill switch process running")
        processes = stdout.strip().split('\n')
        for proc in processes:
            if 'kill_switch.py' in proc:
                parts = proc.split()
                if len(parts) >= 2:
                    pid = parts[1]
                    print(f"    PID: {pid}")
        kill_switch_ok = True
    else:
        print(f"  ❌ Kill switch not running")
        kill_switch_ok = False
    
    return kill_switch_ok

def overall_health_check():
    """Complete system health check"""
    print("="*60)
    print("🏥 COMPREHENSIVE SYSTEM HEALTH CHECK")
    print(f"🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Check all components
    containers_ok, containers = check_container_status()
    bridge_ok, bridge_details = check_whatsapp_bridge()
    monitor_ok, monitor_details = check_drop_monitor()
    sheets_ok = check_google_sheets()
    kill_switch_ok = check_kill_switch()
    
    print("\n" + "="*60)
    print("📊 OVERALL SYSTEM STATUS:")
    print("="*60)
    
    components = [
        ("Docker Containers", containers_ok),
        ("WhatsApp Bridge", bridge_ok),
        ("Drop Monitor", monitor_ok),
        ("Google Sheets", sheets_ok),
        ("Kill Switch", kill_switch_ok)
    ]
    
    all_healthy = True
    for name, status in components:
        icon = "✅" if status else "❌"
        print(f"  {icon} {name}: {'HEALTHY' if status else 'UNHEALTHY'}")
        if not status:
            all_healthy = False
    
    print("\n" + "="*60)
    if all_healthy:
        print("🎉 SYSTEM STATUS: ALL SERVICES HEALTHY AND FUNCTIONAL")
        print("✅ Ready for testing!")
    else:
        print("⚠️  SYSTEM STATUS: ISSUES DETECTED")
        print("❌ System not ready for reliable testing")
    print("="*60)
    
    return all_healthy

if __name__ == "__main__":
    healthy = overall_health_check()
    exit(0 if healthy else 1)