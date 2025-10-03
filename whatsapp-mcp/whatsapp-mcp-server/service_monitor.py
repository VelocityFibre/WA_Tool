#!/usr/bin/env python3
"""
WA_Tool Service Monitoring Dashboard
===================================

Streamlit dashboard to monitor the status of all WhatsApp monitoring services
for Lawley, Velo Test, and Mohadin groups.
"""

import streamlit as st
import subprocess
import psutil
import time
import os
import json
from datetime import datetime
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="WA_Tool Service Monitor",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.metric-container {
    background-color: #f0f2f6;
    border: 1px solid #e0e0e0;
    padding: 1rem;
    border-radius: 0.5rem;
    text-align: center;
}
.status-running {
    color: #00C851;
    font-weight: bold;
}
.status-stopped {
    color: #ff4444;
    font-weight: bold;
}
.status-warning {
    color: #ff8800;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Service definitions
SERVICES = {
    "whatsapp-bridge": {
        "name": "WhatsApp Bridge",
        "description": "Core WhatsApp integration service",
        "location": "../whatsapp-bridge/whatsapp-bridge",
        "groups": ["All"],
        "critical": True
    },
    "realtime_drop_monitor": {
        "name": "Real-time Drop Monitor",
        "description": "Monitors all groups for DR numbers",
        "script": "realtime_drop_monitor.py --interval 15",
        "groups": ["Lawley", "Velo Test", "Mohadin"],
        "critical": True
    },
    "google_sheets_qa_monitor": {
        "name": "Google Sheets QA Monitor",
        "description": "Monitors sheets for incomplete drops",
        "script": "google_sheets_qa_monitor.py --interval 60",
        "groups": ["Velo Test", "Mohadin"],
        "critical": True
    },
    "whatsapp_message_monitor": {
        "name": "Velo Test Resubmission Monitor",
        "description": "Monitors Velo Test for resubmissions",
        "script": "whatsapp_message_monitor.py --interval 30",
        "groups": ["Velo Test"],
        "critical": False
    },
    "mohadin_message_monitor": {
        "name": "Mohadin Resubmission Monitor",
        "description": "Monitors Mohadin for resubmissions",
        "script": "mohadin_message_monitor.py --interval 30",
        "groups": ["Mohadin"],
        "critical": False
    }
}

GROUPS = {
    "Lawley": {"color": "#2E86AB", "jid": "120363418298130331@g.us"},
    "Velo Test": {"color": "#A23B72", "jid": "120363421664266245@g.us"},
    "Mohadin": {"color": "#F18F01", "jid": "120363421532174586@g.us"}
}

def check_service_status(service_name, service_info):
    """Check if a service is running"""
    try:
        if service_name == "whatsapp-bridge":
            # Check for whatsapp-bridge process
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] == 'whatsapp-bridge' or proc.info['name'] == './whatsapp-bridge':
                    return True, proc.info['pid'], "Running"
        else:
            # Check for Python scripts
            script_name = service_info["script"].split()[0]
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['name'] and 'python' in proc.info['name'].lower():
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if script_name in cmdline:
                        return True, proc.info['pid'], "Running"

        return False, None, "Stopped"

    except Exception as e:
        return False, None, f"Error: {str(e)}"

def get_last_log_info(script_name):
    """Get last log entry info for a script"""
    log_files = {
        "realtime_drop_monitor": "realtime_monitor.log",
        "google_sheets_qa_monitor": "google_sheets_qa_monitor.log",
        "whatsapp_message_monitor": "whatsapp_message_monitor.log",
        "mohadin_message_monitor": "mohadin_message_monitor.log"
    }

    log_file = log_files.get(script_name)
    if log_file and os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    return last_line
        except Exception:
            pass

    return "No log data available"

def get_database_stats():
    """Get statistics from the database"""
    try:
        import sqlite3
        conn = sqlite3.connect('../whatsapp-bridge/store/messages.db')
        cursor = conn.cursor()

        # Get message counts by group
        cursor.execute("""
            SELECT c.name, COUNT(m.id) as message_count
            FROM chats c
            LEFT JOIN messages m ON c.jid = m.chat_jid
            WHERE c.jid IN ('120363418298130331@g.us', '120363421664266245@g.us', '120363421532174586@g.us')
            GROUP BY c.jid, c.name
        """)

        results = cursor.fetchall()
        conn.close()

        return dict(results)
    except Exception as e:
        return {"Error": str(e)}

def get_monitor_state():
    """Get monitor state information"""
    try:
        if os.path.exists('monitor_state.json'):
            with open('monitor_state.json', 'r') as f:
                state = json.load(f)
                return {
                    "last_check": state.get("last_check_time", "Unknown"),
                    "processed_messages": len(state.get("processed_message_ids", []))
                }
    except Exception:
        pass
    return {"last_check": "Unknown", "processed_messages": 0}

# Header
st.title("📱 WA_Tool Service Monitoring Dashboard")
st.markdown(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Service Status Overview
st.header("🔍 Service Status Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    total_services = len(SERVICES)
    st.metric("Total Services", total_services)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    running_count = sum(1 for s in SERVICES.values() if check_service_status("", s)[0])
    st.metric("Running Services", running_count)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    critical_services = [s for s in SERVICES.values() if s.get("critical", False)]
    critical_running = sum(1 for s in critical_services if check_service_status("", s)[0])
    st.metric("Critical Services", f"{critical_running}/{len(critical_services)}")
    st.markdown('</div>', unsafe_allow_html=True)

# Detailed Service Status
st.header("📋 Detailed Service Status")

for service_name, service_info in SERVICES.items():
    is_running, pid, status = check_service_status(service_name, service_info)
    status_class = "status-running" if is_running else "status-stopped"

    with st.expander(f"{service_info['name']} - <span class='{status_class}'>{status}</span>", expanded=True):
        col1, col2 = st.columns([2, 1])

        with col1:
            st.write(f"**Description:** {service_info['description']}")
            st.write(f"**Monitors:** {', '.join(service_info['groups'])}")
            if 'script' in service_info:
                st.write(f"**Command:** `{service_info['script']}`")
            if 'location' in service_info:
                st.write(f"**Location:** `{service_info['location']}`")
            st.write(f"**Critical:** {'🔴 Yes' if service_info.get('critical') else '🟡 No'}")

        with col2:
            if is_running:
                st.success(f"🟢 RUNNING (PID: {pid})")
            else:
                st.error("🔴 STOPPED")

                # Show start button for stopped services
                if st.button(f"Start {service_info['name']}", key=f"start_{service_name}"):
                    if 'script' in service_info:
                        command = f"source .venv/bin/activate && python {service_info['script']}"
                        st.info(f"Run in terminal: `{command}`")

        # Show last log info
        if 'script' in service_info:
            script_name = service_info['script'].split()[0]
            last_log = get_last_log_info(script_name)
            st.code(last_log[:200] + "..." if len(last_log) > 200 else last_log)

# Group Status
st.header("📊 WhatsApp Group Status")

db_stats = get_database_stats()
for group_name, group_info in GROUPS.items():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown(f"### {group_name}")
        st.markdown(f"**JID:** `{group_info['jid']}`")

    with col2:
        message_count = db_stats.get(f"{group_name} Activations", 0) or db_stats.get(group_name, 0)
        st.markdown(f"**Messages in Database:** {message_count}")

    with col3:
        # Create status indicator based on recent activity
        if message_count > 0:
            st.success("🟢 Active")
        else:
            st.warning("🟡 No Messages")

# System Information
st.header("ℹ️ System Information")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Monitor State")
    monitor_state = get_monitor_state()
    st.write(f"**Last Check:** {monitor_state['last_check']}")
    st.write(f"**Processed Messages:** {monitor_state['processed_messages']}")

with col2:
    st.subheader("Database Status")
    try:
        import sqlite3
        conn = sqlite3.connect('../whatsapp-bridge/store/messages.db')
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM chats")
        total_chats = cursor.fetchone()[0]

        st.write(f"**Total Messages:** {total_messages}")
        st.write(f"**Total Chats:** {total_chats}")

        conn.close()
    except Exception as e:
        st.error(f"Database Error: {e}")

# Auto-refresh
st.header("🔄 Auto-Refresh")
refresh_interval = st.selectbox("Refresh Interval (seconds)", [30, 60, 120, 300], index=1)

if st.button("Refresh Now"):
    st.rerun()

# Auto-refresh using JavaScript
st.markdown(f"""
<script>
    setTimeout(function() {{
        location.reload();
    }}, {refresh_interval * 1000});
</script>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("**WA_Tool Monitoring Dashboard** - Monitoring WhatsApp groups for Lawley, Velo Test, and Mohadin")
st.markdown(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")