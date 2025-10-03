#!/bin/bash
#
# Add Mohadin Group JID to System Configuration
# Usage: ./add_mohadin_jid.sh "120363XXXXXXXXX@g.us"
#

if [ $# -ne 1 ]; then
    echo "Usage: $0 \"MOHADIN_GROUP_JID\""
    echo "Example: $0 \"120363123456789@g.us\""
    exit 1
fi

MOHADIN_JID="$1"

echo "🔧 Adding Mohadin group JID: $MOHADIN_JID"
echo ""

# Update realtime_drop_monitor.py
echo "1. Updating realtime_drop_monitor.py..."
sed -i "s/MOHADIN_GROUP_JID_PLACEHOLDER/$MOHADIN_JID/g" realtime_drop_monitor.py

# Update qa_feedback_communicator.py  
echo "2. Updating qa_feedback_communicator.py..."
sed -i "s/MOHADIN_GROUP_JID_PLACEHOLDER/$MOHADIN_JID/g" qa_feedback_communicator.py

echo "3. Restarting services..."
sudo systemctl restart whatsapp-drop-monitor
sudo systemctl restart google-sheets-qa-monitor

echo ""
echo "✅ Mohadin integration complete!"
echo ""
echo "🎯 System now monitors:"
echo "  • Lawley: 120363418298130331@g.us"
echo "  • Velo Test: 120363421664266245@g.us" 
echo "  • Mohadin: $MOHADIN_JID"
echo ""
echo "📊 Google Sheets integration active for:"
echo "  • Velo Test sheet"
echo "  • Mohadin sheet"
echo ""
echo "🚀 System is LIVE for all three projects!"