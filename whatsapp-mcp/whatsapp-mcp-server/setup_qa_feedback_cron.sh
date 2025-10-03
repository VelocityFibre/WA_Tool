#!/bin/bash
"""
Setup QA Feedback Automation - 30 Minute Intervals
This script adds a cron job to automatically check for incomplete QA reviews
and send WhatsApp feedback every 30 minutes.
"""

echo "🕒 Setting up QA Feedback automation for 30-minute intervals..."

# Define the cron job
CRON_COMMAND="*/30 * * * * cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server && python3 run_qa_feedback_check.py >> qa_feedback_cron.log 2>&1"

# Add to crontab (preserve existing crontab)
(crontab -l 2>/dev/null; echo "$CRON_COMMAND") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "📋 QA Feedback will now run automatically every 30 minutes"
echo "📁 Logs will be saved to: qa_feedback_cron.log"
echo ""
echo "🔧 To view current cron jobs:"
echo "   crontab -l"
echo ""
echo "📊 To monitor logs:"
echo "   tail -f qa_feedback_cron.log"
echo ""
echo "⏹️  To remove automation:"
echo "   crontab -e (then delete the qa_feedback line)"
echo ""
echo "🎯 Your QA feedback system is now automated for 30-minute response!"