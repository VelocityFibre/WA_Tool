#!/usr/bin/env python3
"""
Automated QA Feedback Checker
Runs the QA feedback communicator to check for incomplete installations
and send WhatsApp messages as needed.

This script can be run via cron for automated checking.
"""

import subprocess
import sys
import os
from datetime import datetime

def run_qa_feedback_check():
    """Run the QA feedback check process."""
    
    print(f"🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Starting QA feedback check...")
    
    # Path to the QA feedback communicator
    script_path = os.path.join(os.path.dirname(__file__), 'qa_feedback_communicator.py')
    
    try:
        # Run the QA feedback communicator in live mode
        result = subprocess.run([
            '/home/louisdup/.local/bin/uv', 'run', 'python', script_path,
            '--hours', '2'  # Check last 2 hours (30min intervals)
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print("✅ QA feedback check completed successfully")
            if result.stdout:
                print("Output:", result.stdout)
        else:
            print("❌ QA feedback check failed")
            if result.stderr:
                print("Error:", result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running QA feedback check: {e}")
        return False

if __name__ == "__main__":
    success = run_qa_feedback_check()
    sys.exit(0 if success else 1)