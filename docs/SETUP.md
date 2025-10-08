# WA_Tool Setup Guide - Version 3.0.0

Complete step-by-step setup instructions for the WhatsApp Drop Monitoring & QA Automation System.

## 📋 Prerequisites Checklist

Before starting, ensure you have the following accounts and software installed:

### Required Software
- [ ] **Go** 1.19+ ([Download](https://golang.org/dl/))
- [ ] **Python** 3.11+ ([Download](https://python.org/downloads/))
- [ ] **Node.js** & npm ([Download](https://nodejs.org/))
- [ ] **Docker** & Docker Compose ([Download](https://docs.docker.com/get-docker/))
- [ ] **UV** Python package manager ([Install](https://docs.astral.sh/uv/))

### Required Accounts
- [ ] **Google Cloud Console** account
- [ ] **Neon PostgreSQL** database account
- [ ] **OpenRouter** API account (for AI features)
- [ ] **GitHub** account (for repository access)

---

## 🗄️ Step 1: Database Setup (Neon PostgreSQL)

### 1.1 Create Neon Database

1. **Sign up for Neon**
   - Go to [neon.tech](https://neon.tech)
   - Create an account and verify your email

2. **Create New Project**
   ```bash
   Project Name: WA_Tool_Production
   Region: US East (recommended for performance)
   PostgreSQL Version: Latest (15+)
   ```

3. **Get Connection String**
   - Navigate to **Dashboard** → **Connection Details**
   - Copy the connection string (format shown below):
   ```
   postgresql://username:password@ep-example-123456.us-east-1.aws.neon.tech/dbname?sslmode=require
   ```

### 1.2 Test Database Connection

```bash
# Install psycopg2 for testing
pip install psycopg2-binary

# Test connection (replace with your actual connection string)
python3 -c "
import psycopg2
conn = psycopg2.connect('postgresql://username:password@ep-example.us-east-1.aws.neon.tech/dbname?sslmode=require')
print('✅ Database connection successful!')
conn.close()
"
```

### 1.3 Database Schema Creation

The application will automatically create the required tables on first run:

```sql
-- Tables created automatically:
-- 1. neon_installations - for tracking drop installations
-- 2. qa_photo_reviews - for tracking QA feedback workflow
```

---

## 📊 Step 2: Google Sheets API Setup

### 2.1 Create Google Cloud Project

1. **Access Google Cloud Console**
   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - Sign in with your Google account

2. **Create New Project**
   ```bash
   Project Name: WA-Tool-Sheets-Integration
   Project ID: wa-tool-sheets-123 (auto-generated)
   Organization: (leave blank for personal projects)
   ```

3. **Enable Google Sheets API**
   - Navigate to **APIs & Services** → **Library**
   - Search for "Google Sheets API"
   - Click **Enable**

### 2.2 Create Service Account

1. **Navigate to Service Accounts**
   - Go to **IAM & Admin** → **Service Accounts**
   - Click **Create Service Account**

2. **Configure Service Account**
   ```bash
   Service account name: wa-tool-sheets-access
   Service account ID: wa-tool-sheets-access (auto-filled)
   Description: Service account for WA_Tool Google Sheets integration
   ```

3. **Assign Role**
   - Click **Create and Continue**
   - Role: **Editor** (or create custom role with Sheets permissions)
   - Click **Continue** → **Done**

### 2.3 Generate Credentials

1. **Create Key**
   - Click on your newly created service account
   - Go to **Keys** tab
   - Click **Add Key** → **Create New Key**
   - Choose **JSON** format
   - Click **Create**

2. **Save Credentials File**
   ```bash
   # Download will save as: wa-tool-sheets-access-xxxxx.json
   # Rename and move to your WA_Tool directory:
   mv ~/Downloads/wa-tool-sheets-access-xxxxx.json /path/to/WA_Tool/credentials.json
   ```

### 2.4 Create and Configure Spreadsheet

1. **Create Google Spreadsheet**
   - Go to [sheets.google.com](https://sheets.google.com)
   - Click **Blank** to create new spreadsheet
   - Name it: "WA Tool - Drop Tracking"

2. **Set up Sheets Structure**
   
   Create these tabs:
   - **Velo Test** (for Velo Test project drops)
   - **Lawley** (for Lawley project drops)

3. **Configure Column Headers** (both sheets)
   ```
   A: Date
   B: Drop Number  
   C: Contractor
   D: Project
   E: Status
   ...
   V: Incomplete (QA status)
   W: Resubmitted (Resubmission tracking)
   X: Completed (Final completion status)
   ```

4. **Share with Service Account**
   - Click **Share** button
   - Add the service account email (from credentials.json):
     ```
     wa-tool-sheets-access@wa-tool-sheets-123.iam.gserviceaccount.com
     ```
   - Set permission to **Editor**
   - Click **Send**

5. **Get Spreadsheet ID**
   - Copy the ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk/edit
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                        This is your GOOGLE_SHEETS_ID
   ```

---

## 🤖 Step 3: AI Integration Setup (OpenRouter)

### 3.1 Create OpenRouter Account

1. **Sign up for OpenRouter**
   - Go to [openrouter.ai](https://openrouter.ai)
   - Click **Sign Up**
   - Verify your email address

2. **Add Credits to Account**
   - Go to **Billing** → **Add Credits**
   - Add minimum $5 for testing (recommended $20 for production)

### 3.2 Generate API Key

1. **Create API Key**
   - Go to **API Keys** in dashboard
   - Click **Create Key**
   - Name: "WA_Tool_Production"
   - Click **Create**

2. **Save API Key Securely**
   ```bash
   # API key format: sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   # Never commit this to version control!
   ```

### 3.3 Test API Connection

```bash
# Test OpenRouter connection
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "x.ai/grok-2-1212:free",
       "messages": [{"role": "user", "content": "Test connection"}]
     }' \
     https://openrouter.ai/api/v1/chat/completions
```

---

## ⚙️ Step 4: Application Installation

### 4.1 Clone Repository

```bash
# Clone the repository
git clone https://github.com/VelocityFibre/WA_Tool.git
cd WA_Tool

# Check you're on the latest version
git log --oneline -5
# Should show Version 3.0.0 commits from 8 Oct 2025
```

### 4.2 Environment Configuration

1. **Copy Environment Template**
   ```bash
   cp .env.example .env
   ```

2. **Edit Configuration File**
   ```bash
   nano .env  # or your preferred editor
   ```

3. **Update Key Variables**
   ```bash
   # Database Configuration
   NEON_DATABASE_URL=postgresql://your_username:your_password@ep-example.us-east-1.aws.neon.tech/your_database?sslmode=require
   
   # Google Sheets Integration
   GOOGLE_SHEETS_CREDENTIALS_PATH=/full/path/to/credentials.json
   GOOGLE_SHEETS_ID=1TYxDLyCqDHr0Imb5j7X4uJhxccgJTO0KrDVAD0Ja0Dk
   
   # AI Configuration
   LLM_API_KEY=sk-or-v1-your-openrouter-api-key-here
   LLM_PROVIDER=openrouter
   LLM_MODEL=x.ai/grok-2-1212:free
   
   # Project Settings
   PROJECT_GROUPS=Velo Test,Lawley
   DEFAULT_PROJECT=Velo Test
   ```

### 4.3 Install Dependencies

#### Python Dependencies
```bash
# Navigate to MCP server directory
cd whatsapp-mcp/whatsapp-mcp-server

# Create virtual environment
uv venv --python 3.11 venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install requirements
uv pip install -r requirements.txt
cd ../..
```

#### Go Dependencies
```bash
# Navigate to bridge directory
cd whatsapp-mcp/whatsapp-bridge

# Initialize and install Go modules
go mod download
go mod tidy
cd ../..
```

---

## 🚀 Step 5: First Run and Testing

### 5.1 Start the Application

```bash
# Make start script executable
chmod +x start_wa_tool.sh

# Start all services
./start_wa_tool.sh
```

### 5.2 Connect WhatsApp

1. **Look for QR Code in Terminal**
   - The bridge service will display a QR code
   - You have 60 seconds to scan it

2. **Scan with WhatsApp**
   - Open WhatsApp on your phone
   - Go to **Settings** → **Linked Devices**
   - Tap **Link a Device**
   - Scan the QR code displayed in terminal

3. **Verify Connection**
   - Check terminal for "✅ WhatsApp Connected" message
   - Verify in **logs/bridge.log** for connection status

### 5.3 Verify Services

```bash
# Check all services are running
ps aux | grep -E "(go run|python.*main.py|python.*drop_monitor)"

# Check service endpoints
curl http://localhost:8080/status  # WhatsApp Bridge
curl http://localhost:5000/api/status  # Backend API
curl http://localhost:3001  # Frontend Interface
```

### 5.4 Test Database Connection

```bash
# Run database test
cd whatsapp-mcp/whatsapp-mcp-server
python3 -c "
from neon_database import test_connection
if test_connection():
    print('✅ Database connection successful!')
else:
    print('❌ Database connection failed!')
"
```

### 5.5 Test Google Sheets Integration

```bash
# Test Sheets access
python3 -c "
from google_sheets_service import test_access
if test_access():
    print('✅ Google Sheets access successful!')
else:
    print('❌ Google Sheets access failed!')
"
```

---

## 🧪 Step 6: End-to-End Workflow Testing

### 6.1 Test Drop Detection (Phase 1)

1. **Post Test Message in WhatsApp Group**
   ```
   Message: "DR9999999"
   Expected: System detects drop number and creates records
   ```

2. **Verify Results**
   ```bash
   # Check logs
   tail -f whatsapp-mcp/whatsapp-mcp-server/logs/drop_monitor.log
   
   # Verify Google Sheets entry
   # Check your spreadsheet for new row with DR9999999
   
   # Verify database record
   # Should see new installation record in Neon dashboard
   ```

### 6.2 Test QA Feedback (Phase 2)

1. **Mark Drop as Incomplete**
   - Go to Google Sheets
   - Find the DR9999999 row
   - Set Column V (Incomplete) to TRUE

2. **Verify Feedback Sent**
   ```bash
   # Check QA monitor logs
   tail -f whatsapp-mcp/whatsapp-mcp-server/logs/qa_feedback.log
   
   # Should see:
   # - Incomplete status detected
   # - Feedback message generated
   # - Message sent to agent
   ```

### 6.3 Test Resubmission Detection (Phase 3)

1. **Post Resubmission Message**
   ```
   Message: "DR9999999 DONE"
   Expected: System updates resubmission status
   ```

2. **Verify Status Update**
   ```bash
   # Check resubmission handler logs
   tail -f whatsapp-mcp/whatsapp-mcp-server/logs/resubmission_handler.log
   
   # Verify Google Sheets update
   # Column W (Resubmitted) should be TRUE
   ```

---

## 🔧 Step 7: Production Configuration

### 7.1 Security Hardening

```bash
# Set proper file permissions
chmod 600 .env
chmod 600 credentials.json

# Create logs directory with proper permissions
mkdir -p logs
chmod 755 logs
```

### 7.2 Service Management

#### Create Systemd Service (Linux)
```bash
# Create service file
sudo nano /etc/systemd/system/wa-tool.service
```

```ini
[Unit]
Description=WA_Tool WhatsApp Drop Monitoring System
After=network.target

[Service]
Type=forking
User=your_username
WorkingDirectory=/path/to/WA_Tool
ExecStart=/path/to/WA_Tool/start_wa_tool.sh
ExecStop=/path/to/WA_Tool/stop_wa_tool.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable wa-tool.service
sudo systemctl start wa-tool.service
sudo systemctl status wa-tool.service
```

### 7.3 Monitoring Setup

```bash
# Set up log rotation
sudo nano /etc/logrotate.d/wa-tool
```

```
/path/to/WA_Tool/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
    postrotate
        /path/to/WA_Tool/restart_services.sh
    endscript
}
```

---

## ✅ Step 8: Verification Checklist

Run through this checklist to ensure everything is working:

### System Health
- [ ] All 6 services are running (bridge, monitors, handlers)
- [ ] WhatsApp connection is active and stable
- [ ] Database connection is working
- [ ] Google Sheets API is accessible
- [ ] OpenRouter AI integration is functional

### Workflow Testing
- [ ] Drop detection works (Phase 1)
- [ ] Google Sheets updates correctly
- [ ] Database records are created
- [ ] QA feedback system works (Phase 2)
- [ ] Resubmission detection works (Phase 3)
- [ ] No duplicate records are created

### Performance Metrics
- [ ] Drop detection speed < 15 seconds
- [ ] QA feedback response < 30 seconds
- [ ] Database queries < 100ms response time
- [ ] Memory usage < 1GB
- [ ] CPU usage < 50%

---

## 🐛 Troubleshooting Common Issues

### WhatsApp Connection Issues
```bash
# Problem: QR code not appearing
# Solution:
cd whatsapp-mcp/whatsapp-bridge
rm -rf store/*  # Clear session data
go run main.go  # Restart with fresh session

# Problem: Connection keeps dropping
# Check if you have too many linked devices (WhatsApp limit is 4)
# Solution: Unlink unused devices in WhatsApp settings
```

### Database Connection Issues
```bash
# Problem: "connection refused" error
# Check connection string format:
echo $NEON_DATABASE_URL
# Should be: postgresql://user:pass@host/db?sslmode=require

# Test network connectivity:
ping your-neon-host.us-east-1.aws.neon.tech

# Verify SSL requirement (Neon requires SSL):
python3 -c "import psycopg2; psycopg2.connect('your-connection-string')"
```

### Google Sheets Permission Errors
```bash
# Problem: 403 Forbidden error
# 1. Check service account email in credentials.json
# 2. Verify spreadsheet is shared with service account
# 3. Ensure Google Sheets API is enabled in Google Cloud Console

# Test Sheets API access:
python3 -c "
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
creds = Credentials.from_service_account_file('credentials.json')
service = build('sheets', 'v4', credentials=creds)
print('✅ Google Sheets API accessible!')
"
```

### AI Integration Issues
```bash
# Problem: OpenRouter API errors
# Check API key validity:
curl -H "Authorization: Bearer $LLM_API_KEY" https://openrouter.ai/api/v1/models

# Check account credits:
curl -H "Authorization: Bearer $LLM_API_KEY" https://openrouter.ai/api/v1/auth/key

# Verify model availability:
curl -H "Authorization: Bearer $LLM_API_KEY" https://openrouter.ai/api/v1/models | grep "x.ai/grok"
```

---

## 📞 Support and Resources

### Documentation
- [Main README](../README.md) - Complete system overview
- [CHANGELOG](../CHANGELOG.md) - Version history and changes
- [API Documentation](API.md) - Detailed API reference

### Getting Help
- **GitHub Issues**: [Submit a bug report or feature request](https://github.com/VelocityFibre/WA_Tool/issues)
- **Discussions**: [Join the community discussion](https://github.com/VelocityFibre/WA_Tool/discussions)

### Useful Links
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Neon PostgreSQL Documentation](https://neon.tech/docs)
- [OpenRouter API Documentation](https://openrouter.ai/docs)
- [WhatsApp Web.js Guide](https://wwebjs.dev/)

---

**🎉 Congratulations! Your WA_Tool Version 3.0.0 is now fully set up and ready for production use!**

*Last updated: 8 October 2025 - Complete QA Workflow System*