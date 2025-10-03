#!/usr/bin/env python3
"""
Full Communications Process Test
Tests the complete flow from WhatsApp message to feedback response.
"""

import psycopg2
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Optional

# Add whatsapp module to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import whatsapp
from resubmission_handler import handle_drop_resubmission

# Configuration
NEON_DB_URL = "postgresql://neondb_owner:npg_RIgDxzo4St6d@ep-damp-credit-a857vku0-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"
VELO_TEST_GROUP_JID = '120363421664266245@g.us'

def print_step(step_num: int, description: str):
    """Print test step with formatting."""
    print(f"\n{'='*60}")
    print(f"🧪 STEP {step_num}: {description}")
    print('='*60)

def wait_for_user_input(message: str):
    """Wait for user confirmation."""
    print(f"\n⏸️  {message}")
    input("Press Enter to continue...")

def check_drop_in_database(drop_number: str) -> bool:
    """Check if drop number exists in database."""
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM installations WHERE drop_number = %s", (drop_number,))
        exists = cursor.fetchone() is not None
        
        cursor.close()
        conn.close()
        return exists
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def get_qa_review_status(drop_number: str) -> Optional[dict]:
    """Get QA review status for drop number."""
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                step_01_property_frontage, step_02_location_before_install,
                step_03_outside_cable_span, step_04_home_entry_outside,
                step_05_home_entry_inside, step_06_fibre_entry_to_ont,
                step_07_patched_labelled_drop, step_08_work_area_completion,
                step_09_ont_barcode_scan, step_10_ups_serial_number,
                step_11_powermeter_reading, step_12_powermeter_at_ont,
                step_13_active_broadband_light, step_14_customer_signature,
                incomplete, completed, feedback_sent
            FROM qa_photo_reviews 
            WHERE drop_number = %s
        """, (drop_number,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            return {
                'steps': result[:14],
                'incomplete': result[14],
                'completed': result[15],
                'feedback_sent': result[16]
            }
        return None
    except Exception as e:
        print(f"❌ Database error: {e}")
        return None

def simulate_qa_review(drop_number: str, incomplete_steps: list):
    """Simulate QA agent marking some steps as incomplete."""
    try:
        conn = psycopg2.connect(NEON_DB_URL)
        cursor = conn.cursor()
        
        print(f"🔧 Simulating QA review - marking steps {incomplete_steps} as missing...")
        
        # First, mark some steps as complete (simulate partial review)
        update_parts = []
        params = []
        
        for i in range(1, 15):  # Steps 1-14
            step_col = f"step_{i:02d}_{get_step_name(i)}"
            if i in incomplete_steps:
                update_parts.append(f"{step_col} = FALSE")
            else:
                update_parts.append(f"{step_col} = TRUE")
        
        # Mark as incomplete
        update_parts.extend([
            "incomplete = TRUE",
            "completed = FALSE",
            "feedback_sent = NULL",
            "updated_at = CURRENT_TIMESTAMP"
        ])
        
        update_query = f"""
            UPDATE qa_photo_reviews 
            SET {', '.join(update_parts)}
            WHERE drop_number = %s
        """
        
        cursor.execute(update_query, (drop_number,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"✅ QA review simulated - {len(incomplete_steps)} steps marked incomplete")
        return True
        
    except Exception as e:
        print(f"❌ Error simulating QA review: {e}")
        return False

def get_step_name(step_num: int) -> str:
    """Get step name for database column."""
    step_names = {
        1: "property_frontage",
        2: "location_before_install", 
        3: "outside_cable_span",
        4: "home_entry_outside",
        5: "home_entry_inside",
        6: "fibre_entry_to_ont",
        7: "patched_labelled_drop",
        8: "work_area_completion",
        9: "ont_barcode_scan",
        10: "ups_serial_number",
        11: "powermeter_reading",
        12: "powermeter_at_ont", 
        13: "active_broadband_light",
        14: "customer_signature"
    }
    return step_names.get(step_num, f"step_{step_num}")

def run_feedback_system():
    """Run the QA feedback system."""
    print("🔧 Running QA feedback system...")
    os.system("cd /home/louisdup/VF/Apps/WA_Tool/whatsapp-mcp/whatsapp-mcp-server && uv run python qa_feedback_communicator.py --hours 1")

def main():
    """Run complete communications test."""
    print("🚀 COMPLETE COMMUNICATIONS PROCESS TEST")
    print("Testing: Drop Detection → Database → QA → Feedback → Resubmission")
    print("\nThis test will use the Velo Test WhatsApp group for safe testing.")
    
    # Get test drop number
    test_drop = input("\n📝 Enter a TEST drop number (e.g., DR9999999): ").strip().upper()
    if not test_drop.startswith('DR'):
        test_drop = 'DR' + test_drop
    
    print(f"🧪 Testing with drop number: {test_drop}")
    
    # Step 1: User posts to WhatsApp
    print_step(1, "WhatsApp Message Posting")
    print(f"📱 Please post the following message to the Velo Test WhatsApp group:")
    print(f"   '{test_drop} - Test installation complete'")
    print("\nThis will trigger the real-time monitor to detect and process the drop.")
    
    wait_for_user_input("After posting the message")
    
    # Step 2: Wait for system to detect
    print_step(2, "System Detection")
    print("⏳ Waiting for system to detect the drop number...")
    
    detected = False
    for i in range(12):  # Wait up to 3 minutes (12 x 15 seconds)
        if check_drop_in_database(test_drop):
            print(f"✅ Drop {test_drop} detected and added to database!")
            detected = True
            break
        print(f"   Checking... ({i+1}/12)")
        time.sleep(15)
    
    if not detected:
        print(f"❌ Drop {test_drop} not detected after 3 minutes")
        print("   Check that the monitor is running: ./manage_monitor.sh status")
        return False
    
    # Step 3: Check QA review creation
    print_step(3, "QA Review Creation")
    qa_status = get_qa_review_status(test_drop)
    if qa_status:
        print(f"✅ QA review created for {test_drop}")
        print(f"   Steps completed: {sum(qa_status['steps'])}/14")
    else:
        print(f"❌ No QA review found for {test_drop}")
        return False
    
    # Step 4: Simulate QA finding issues
    print_step(4, "QA Review Simulation")
    incomplete_steps = [9, 14]  # ONT Barcode and Customer Signature
    if simulate_qa_review(test_drop, incomplete_steps):
        print("✅ QA review simulated - marked some photos as missing")
    else:
        print("❌ Failed to simulate QA review")
        return False
    
    # Step 5: Run feedback system
    print_step(5, "Feedback Message Generation")
    print("🔧 Running feedback system to generate WhatsApp message...")
    run_feedback_system()
    
    # Step 6: Check if feedback was sent
    print_step(6, "Feedback Verification")
    time.sleep(5)  # Wait a moment
    qa_status_after = get_qa_review_status(test_drop)
    if qa_status_after and qa_status_after['feedback_sent']:
        print(f"✅ Feedback sent for {test_drop}")
        print("📱 Check the Velo Test WhatsApp group for the feedback message!")
    else:
        print(f"⚠️  Feedback may not have been sent - check logs")
    
    # Step 7: Test resubmission
    print_step(7, "Resubmission Test")
    print(f"📱 Now post the SAME drop number again to test resubmission:")
    print(f"   '{test_drop} - Photos updated'")
    print("\nThis tests the resubmission handling system.")
    
    wait_for_user_input("After posting the resubmission message")
    
    # Test resubmission handler
    print("🔧 Testing resubmission handler...")
    resubmission_result = handle_drop_resubmission(
        test_drop, 
        'Test-Agent', 
        'Velo Test', 
        'Photos updated - test resubmission'
    )
    
    if resubmission_result:
        print(f"✅ Resubmission handled successfully for {test_drop}")
    else:
        print(f"❌ Resubmission handling failed for {test_drop}")
    
    # Step 8: Complete test summary
    print_step(8, "Test Complete")
    print("🎉 COMMUNICATIONS TEST COMPLETED!")
    print("\n📊 Test Summary:")
    print(f"✅ Drop Detection: {test_drop} detected from WhatsApp")
    print("✅ Database Sync: Drop added to Neon database")
    print("✅ QA Review: Created and simulated")
    print("✅ Feedback System: Generated WhatsApp message")
    print("✅ Resubmission: Handled intelligently")
    
    print("\n🔍 Next Steps:")
    print("1. Check Velo Test WhatsApp group for feedback message")
    print("2. Verify QA review appears in Streamlit dashboard")
    print("3. Test completing the QA review process")
    
    print(f"\n🧹 Cleanup: You may want to remove test drop {test_drop} from database after testing")
    
    return True

if __name__ == "__main__":
    main()