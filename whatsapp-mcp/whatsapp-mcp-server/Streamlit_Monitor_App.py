#!/usr/bin/env python3
"""
WA_Tool Visual Monitoring Dashboard
==================================
Comprehensive Streamlit dashboard for monitoring WhatsApp group processing workflows
with real-time status, message flow visualization, and system health monitoring.

Date: October 1, 2025
Version: 2.0.0
"""

import streamlit as st
import psutil
import pandas as pd
import sqlite3
import json
import time
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="WA_Tool Monitor Dashboard",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
.metric-card {
    background-color: #f8f9fa;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #007bff;
}
.status-running {
    color: #28a745;
    font-weight: bold;
}
.status-stopped {
    color: #dc3545;
    font-weight: bold;
}
.workflow-step {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 1rem;
    border-radius: 0.5rem;
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

# Service configuration
SERVICES = {
    'WhatsApp Bridge': {
        'process_name': 'whatsapp-bridge',
        'script_path': '../whatsapp-bridge/whatsapp-bridge',
        'critical': True,
        'description': 'Bridge between WhatsApp Web and monitoring system',
        'log_file': '../whatsapp-bridge/bridge.log'
    },
    'Real-time Drop Monitor': {
        'process_name': 'realtime_drop_monitor.py',
        'script_path': 'realtime_drop_monitor.py',
        'critical': True,
        'description': 'Extract DR numbers and sync to database/Google Sheets',
        'log_file': 'realtime_monitor.log'
    },
    'Google Sheets QA Monitor': {
        'process_name': 'google_sheets_qa_monitor.py',
        'script_path': 'google_sheets_qa_monitor.py',
        'critical': True,
        'description': 'Monitor Google Sheets for incomplete drops and send feedback',
        'log_file': 'google_sheets_qa_monitor.log'
    },
    'Velo Test Resubmission Monitor': {
        'process_name': 'whatsapp_message_monitor.py',
        'script_path': 'whatsapp_message_monitor.py',
        'critical': False,
        'description': 'Monitor Velo Test for resubmission keywords',
        'log_file': 'whatsapp_message_monitor.log'
    },
    'Mohadin Resubmission Monitor': {
        'process_name': 'mohadin_message_monitor.py',
        'script_path': 'mohadin_message_monitor.py',
        'critical': False,
        'description': 'Monitor Mohadin for resubmission keywords',
        'log_file': 'mohadin_message_monitor.log'
    }
}

# WhatsApp groups configuration
WHATSAPP_GROUPS = {
    'Lawley Activation 3': {
        'jid': '120363418298130331@g.us',
        'project': 'Lawley',
        'color': '#28a745'
    },
    'Velo Test': {
        'jid': '120363421664266245@g.us',
        'project': 'Velo Test',
        'color': '#007bff'
    },
    'Mohadin Activations': {
        'jid': '120363421532174586@g.us',
        'project': 'Mohadin',
        'color': '#dc3545'
    }
}

class WhatsAppMonitor:
    def __init__(self):
        self.db_path = '../whatsapp-bridge/store/messages.db'

    def get_service_status(self, service_config):
        """Check if a service is running and get its details."""
        process_name = service_config['process_name']

        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if process_name in cmdline:
                    return {
                        'status': 'running',
                        'pid': proc.info['pid'],
                        'cpu_percent': proc.cpu_percent(),
                        'memory_mb': proc.memory_info().rss / 1024 / 1024,
                        'uptime': datetime.now() - datetime.fromtimestamp(proc.create_time())
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {'status': 'stopped', 'pid': None, 'cpu_percent': 0, 'memory_mb': 0}

    def get_recent_log_entries(self, log_file, lines=5):
        """Get recent log entries from a log file."""
        try:
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) >= lines else all_lines
        except Exception as e:
            return [f"Error reading log: {e}"]
        return []

    def get_whatsapp_stats(self):
        """Get WhatsApp message statistics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total messages
            cursor.execute("SELECT COUNT(*) FROM messages")
            total_messages = cursor.fetchone()[0]

            # Messages per group
            stats = {}
            for group_name, group_info in WHATSAPP_GROUPS.items():
                cursor.execute("""
                    SELECT COUNT(*) FROM messages
                    WHERE chat_jid = ? AND timestamp > ?
                """, (group_info['jid'], int((datetime.now() - timedelta(hours=24)).timestamp() * 1000)))

                count = cursor.fetchone()[0]
                stats[group_name] = {
                    'messages_24h': count,
                    'jid': group_info['jid'],
                    'color': group_info['color']
                }

            conn.close()
            return {'total_messages': total_messages, 'groups': stats}

        except Exception as e:
            return {'error': str(e)}

    def get_recent_dr_numbers(self, limit=10):
        """Get recent DR numbers from all groups."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get recent DR numbers
            cursor.execute("""
                SELECT m.content, c.name, m.timestamp
                FROM messages m
                JOIN chats c ON m.chat_jid = c.jid
                WHERE m.content LIKE 'DR%'
                ORDER BY m.timestamp DESC
                LIMIT ?
            """, (limit,))

            dr_numbers = []
            for row in cursor.fetchall():
                # Extract DR number from message
                import re
                dr_match = re.search(r'DR\d+', row[0])
                if dr_match:
                    dr_numbers.append({
                        'drop_number': dr_match.group(),
                        'group': row[1],
                        'timestamp': datetime.fromtimestamp(row[2] / 1000),
                        'message': row[0]
                    })

            conn.close()
            return dr_numbers

        except Exception as e:
            return []

    def get_system_metrics(self):
        """Get system performance metrics."""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent
        }

def create_workflow_diagram():
    """Create a visual workflow diagram."""
    st.markdown("### 🔄 Complete Mohadin Workflow")

    # Workflow steps
    workflow_steps = [
        {"step": 1, "title": "Drop Submission", "desc": "Mohadin group posts DR number", "icon": "📝"},
        {"step": 2, "title": "Real-time Detection", "desc": "Monitor detects DR number", "icon": "🔍"},
        {"step": 3, "title": "Database Sync", "desc": "Updates Neon database", "icon": "💾"},
        {"step": 4, "title": "Google Sheets", "desc": "Updates Mohadin tab", "icon": "📊"},
        {"step": 5, "title": "QA Review", "desc": "Checks for incomplete drops", "icon": "✅"},
        {"step": 6, "title": "WhatsApp Feedback", "desc": "Sends feedback to group", "icon": "💬"},
        {"step": 7, "title": "Resubmission", "desc": "Processes resubmissions", "icon": "🔄"}
    ]

    cols = st.columns(len(workflow_steps))

    for i, (col, step) in enumerate(zip(cols, workflow_steps)):
        with col:
            st.markdown(f"""
            <div class="workflow-step" style="text-align: center;">
                <div style="font-size: 2rem;">{step['icon']}</div>
                <div style="font-weight: bold; margin: 0.5rem 0;">{step['step']}</div>
                <div style="font-weight: bold; margin: 0.5rem 0;">{step['title']}</div>
                <div style="font-size: 0.8rem;">{step['desc']}</div>
            </div>
            """, unsafe_allow_html=True)

            if i < len(workflow_steps) - 1:
                st.markdown("<div style='text-align: center; font-size: 1.5rem;'>→</div>", unsafe_allow_html=True)

def main():
    st.title("📱 WA_Tool Monitoring Dashboard")
    st.markdown("---")

    monitor = WhatsAppMonitor()

    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (30s)", value=True)
    if auto_refresh:
        st.rerun()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Select Page", [
        "🏠 Dashboard",
        "📊 Service Status",
        "📱 Message Analytics",
        "🔄 Workflow Monitor",
        "📋 System Metrics"
    ])

    if page == "🏠 Dashboard":
        st.markdown("## 📊 System Overview")

        # Service status overview
        services_running = 0
        services_total = len(SERVICES)

        col1, col2, col3, col4 = st.columns(4)

        for i, (service_name, config) in enumerate(SERVICES.items()):
            col = [col1, col2, col3, col4][i % 4]
            status = monitor.get_service_status(config)

            if status['status'] == 'running':
                services_running += 1
                status_icon = "✅"
                status_class = "status-running"
            else:
                status_icon = "❌"
                status_class = "status-stopped"

            with col:
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{service_name}</h4>
                    <p class="{status_class}">{status_icon} {status['status'].upper()}</p>
                    {f"<small>PID: {status['pid']}</small>" if status['pid'] else ""}
                </div>
                """, unsafe_allow_html=True)

        # Overall system health
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            health_percentage = (services_running / services_total) * 100
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = health_percentage,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "System Health"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            whatsapp_stats = monitor.get_whatsapp_stats()
            if 'error' not in whatsapp_stats:
                st.metric("Total Messages", whatsapp_stats['total_messages'])

                # Group message counts
                for group_name, stats in whatsapp_stats['groups'].items():
                    st.metric(f"{group_name} (24h)", stats['messages_24h'])

        with col3:
            system_metrics = monitor.get_system_metrics()
            st.metric("CPU Usage", f"{system_metrics['cpu_percent']:.1f}%")
            st.metric("Memory Usage", f"{system_metrics['memory_percent']:.1f}%")
            st.metric("Disk Usage", f"{system_metrics['disk_percent']:.1f}%")

        # Recent DR numbers
        st.markdown("### 🕐 Recent DR Numbers")
        recent_drs = monitor.get_recent_dr_numbers()
        if recent_drs:
            df_drs = pd.DataFrame(recent_drs)
            st.dataframe(df_drs[['drop_number', 'group', 'timestamp', 'message']], use_container_width=True)
        else:
            st.info("No recent DR numbers found")

    elif page == "📊 Service Status":
        st.markdown("## 🔧 Service Status Details")

        for service_name, config in SERVICES.items():
            with st.expander(f"{service_name}", expanded=True):
                status = monitor.get_service_status(config)

                col1, col2 = st.columns([2, 1])

                with col1:
                    if status['status'] == 'running':
                        st.success(f"✅ **{service_name} is RUNNING**")
                        st.write(f"**PID:** {status['pid']}")
                        st.write(f"**CPU:** {status['cpu_percent']:.1f}%")
                        st.write(f"**Memory:** {status['memory_mb']:.1f} MB")
                        st.write(f"**Uptime:** {status['uptime']}")
                    else:
                        st.error(f"❌ **{service_name} is STOPPED**")
                        st.write("**Description:**", config['description'])
                        st.write("**Critical:**", "Yes" if config['critical'] else "No")

                with col2:
                    st.write("**Recent Log Entries:**")
                    log_entries = monitor.get_recent_log_entries(config['log_file'])
                    for entry in log_entries:
                        st.code(entry.strip(), language=None)

    elif page == "📱 Message Analytics":
        st.markdown("## 📊 WhatsApp Message Analytics")

        whatsapp_stats = monitor.get_whatsapp_stats()
        if 'error' not in whatsapp_stats:
            # Message distribution chart
            groups_data = []
            for group_name, stats in whatsapp_stats['groups'].items():
                groups_data.append({
                    'Group': group_name,
                    'Messages (24h)': stats['messages_24h'],
                    'Color': stats['color']
                })

            df_groups = pd.DataFrame(groups_data)

            col1, col2 = st.columns(2)

            with col1:
                fig_pie = px.pie(
                    df_groups,
                    values='Messages (24h)',
                    names='Group',
                    title="Message Distribution (24h)"
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                fig_bar = px.bar(
                    df_groups,
                    x='Group',
                    y='Messages (24h)',
                    title="Message Count by Group",
                    color='Group'
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            # Recent DR numbers table
            st.markdown("### 🔍 Recent DR Numbers")
            recent_drs = monitor.get_recent_dr_numbers(limit=20)
            if recent_drs:
                df_drs = pd.DataFrame(recent_drs)
                st.dataframe(df_drs, use_container_width=True)
            else:
                st.info("No DR numbers found in the database")

    elif page == "🔄 Workflow Monitor":
        st.markdown("## 🔄 Mohadin Workflow Monitor")

        create_workflow_diagram()

        st.markdown("---")
        st.markdown("### 📋 Workflow Components Status")

        # Mohadin-specific workflow monitoring
        mohadin_services = {
            'Message Reception': 'WhatsApp Bridge',
            'DR Number Extraction': 'Real-time Drop Monitor',
            'Database Sync': 'Real-time Drop Monitor',
            'Google Sheets Update': 'Real-time Drop Monitor',
            'QA Review': 'Google Sheets QA Monitor',
            'Feedback Communication': 'Google Sheets QA Monitor',
            'Resubmission Processing': 'Mohadin Resubmission Monitor'
        }

        for step, service in mohadin_services.items():
            config = SERVICES[service]
            status = monitor.get_service_status(config)

            if status['status'] == 'running':
                st.success(f"✅ **{step}:** {service} is running")
            else:
                if config['critical']:
                    st.error(f"❌ **{step}:** {service} is CRITICAL and stopped")
                else:
                    st.warning(f"⚠️ **{step}:** {service} is stopped (non-critical)")

    elif page == "📋 System Metrics":
        st.markdown("## 📈 System Performance Metrics")

        system_metrics = monitor.get_system_metrics()

        col1, col2, col3 = st.columns(3)

        with col1:
            fig_cpu = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = system_metrics['cpu_percent'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "CPU Usage (%)"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgreen"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ]
                }
            ))
            st.plotly_chart(fig_cpu, use_container_width=True)

        with col2:
            fig_mem = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = system_metrics['memory_percent'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Memory Usage (%)"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkgreen"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgreen"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ]
                }
            ))
            st.plotly_chart(fig_mem, use_container_width=True)

        with col3:
            fig_disk = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = system_metrics['disk_percent'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Disk Usage (%)"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkred"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgreen"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "red"}
                    ]
                }
            ))
            st.plotly_chart(fig_disk, use_container_width=True)

        # Process details
        st.markdown("### 🔍 Running Processes")

        process_data = []
        for service_name, config in SERVICES.items():
            status = monitor.get_service_status(config)
            if status['status'] == 'running':
                process_data.append({
                    'Service': service_name,
                    'PID': status['pid'],
                    'CPU %': f"{status['cpu_percent']:.1f}",
                    'Memory MB': f"{status['memory_mb']:.1f}",
                    'Uptime': str(status['uptime']).split('.')[0]
                })

        if process_data:
            df_processes = pd.DataFrame(process_data)
            st.dataframe(df_processes, use_container_width=True)
        else:
            st.warning("No services are currently running")

if __name__ == "__main__":
    main()