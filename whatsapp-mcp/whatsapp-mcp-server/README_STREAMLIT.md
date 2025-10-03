# WA_Tool Visual Monitoring Dashboard

📱 **Comprehensive Streamlit dashboard for monitoring WhatsApp group processing workflows**

![Dashboard Preview](https://img.shields.io/badge/Streamlit-Cloud-success?style=for-the-badge&logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

## 🚀 Features

### 📊 **Real-time Service Monitoring**
- Live status of all WhatsApp monitoring services
- Process ID, CPU, and memory usage tracking
- Service uptime monitoring
- Critical service health indicators

### 📱 **WhatsApp Group Analytics**
- Message statistics for all monitored groups
- DR number extraction and tracking
- Message distribution visualization
- Real-time message flow monitoring

### 🔄 **Workflow Visualization**
- Complete Mohadin workflow diagram
- Step-by-step process monitoring
- Component status tracking
- Visual workflow health indicators

### 📈 **System Performance Metrics**
- CPU, memory, and disk usage gauges
- Running process details
- Performance trend visualization
- System health monitoring

## 🏗️ **Monitored Services**

| Service | Description | Critical |
|---------|-------------|----------|
| **WhatsApp Bridge** | Bridge between WhatsApp Web and monitoring system | ✅ Yes |
| **Real-time Drop Monitor** | Extract DR numbers and sync to database/Google Sheets | ✅ Yes |
| **Google Sheets QA Monitor** | Monitor sheets for incomplete drops and send feedback | ✅ Yes |
| **Velo Test Resubmission Monitor** | Monitor Velo Test for resubmission keywords | ❌ No |
| **Mohadin Resubmission Monitor** | Monitor Mohadin for resubmission keywords | ❌ No |

## 📋 **Monitored WhatsApp Groups**

- **Lawley Activation 3** (`120363418298130331@g.us`)
- **Velo Test** (`120363421664266245@g.us`)
- **Mohadin Activations** (`120363421532174586@g.us`)

## 🔄 **Complete Mohadin Workflow**

1. **Drop Submission** → Mohadin group posts DR number
2. **Real-time Detection** → Monitor detects DR number
3. **Database Sync** → Updates Neon database
4. **Google Sheets** → Updates Mohadin tab
5. **QA Review** → Checks for incomplete drops
6. **WhatsApp Feedback** → Sends feedback to group
7. **Resubmission** → Processes resubmissions

## 🚀 **Installation & Setup**

### Local Development

```bash
# Clone the repository
git clone https://github.com/VelocityFibre/WA_chat_monitor_streamlit.git
cd WA_chat_monitor_streamlit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_streamlit.txt

# Run the dashboard
streamlit run Streamlit_Monitor_App.py
```

### Streamlit Cloud Deployment

1. **Fork or clone this repository**
2. **Connect to Streamlit Cloud**
3. **Set up environment variables** (if needed)
4. **Deploy!**

The dashboard will be available at: `https://your-app-name.streamlit.app`

## 🔧 **Configuration**

The dashboard automatically detects and monitors:

- **Service processes** running on the system
- **WhatsApp database** at `../whatsapp-bridge/store/messages.db`
- **Log files** for each service
- **System metrics** via `psutil`

## 📊 **Dashboard Pages**

### 🏠 **Dashboard**
- System overview with all service statuses
- Overall system health gauge
- Recent message statistics
- Latest DR numbers

### 📊 **Service Status**
- Detailed service information
- Process metrics (PID, CPU, Memory)
- Recent log entries
- Critical service alerts

### 📱 **Message Analytics**
- WhatsApp message statistics
- Message distribution charts
- Recent DR numbers table
- Group activity metrics

### 🔄 **Workflow Monitor**
- Visual Mohadin workflow diagram
- Component status tracking
- Step-by-step health indicators
- Critical path monitoring

### 📋 **System Metrics**
- CPU, Memory, Disk usage gauges
- Running processes table
- Performance indicators
- System resource monitoring

## 🎯 **Key Features**

### ✅ **Real-time Monitoring**
- Auto-refresh every 30 seconds
- Live service status updates
- Current message statistics
- Dynamic performance metrics

### 🎨 **Visual Dashboard**
- Interactive charts and gauges
- Color-coded status indicators
- Workflow visualization
- Responsive design

### 📊 **Comprehensive Analytics**
- Message flow tracking
- DR number extraction
- Group activity comparison
- System performance trends

### 🔔 **Status Alerts**
- Critical service failure warnings
- System health indicators
- Process status notifications
- Resource usage alerts

## 🛠️ **Technical Stack**

- **Frontend**: Streamlit
- **Data Processing**: Pandas
- **Visualization**: Plotly
- **System Monitoring**: psutil
- **Database**: SQLite (WhatsApp messages)

## 📝 **Dependencies**

```
streamlit>=1.28.0
psutil>=5.9.0
pandas>=2.0.0
plotly>=5.15.0
```

## 🔍 **Troubleshooting**

### Services Not Showing
- Ensure services are running on the system
- Check if log files are accessible
- Verify database path permissions

### Database Connection Issues
- Check WhatsApp bridge is running
- Verify database file path: `../whatsapp-bridge/store/messages.db`
- Ensure file permissions are correct

### Performance Issues
- Reduce auto-refresh frequency
- Check system resources
- Monitor service memory usage

## 📞 **Support**

For issues or questions:
1. Check the troubleshooting section
2. Verify service statuses
3. Review log files
4. Check system requirements

## 📅 **Version History**

- **v2.0.0** (Oct 1, 2025) - Complete Mohadin workflow monitoring
- **v1.0.0** - Initial release with basic service monitoring

## 📜 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Last Updated**: October 1, 2025
**Version**: 2.0.0
**Maintainer**: Velocity Fibre Team