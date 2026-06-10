"""
Test script for WhatsApp integration
Run this to verify Twilio credentials and test message delivery
"""

import os
import cv2
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.whatsapp_notifier import initialize_whatsapp, send_text_alert, send_alert


def test_credentials():
    """Test if Twilio credentials are available"""
    print("\n" + "="*60)
    print("🔍 CHECKING CREDENTIALS")
    print("="*60)
    
    credentials = {
        "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID"),
        "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN"),
        "TWILIO_WHATSAPP_FROM": os.getenv("TWILIO_WHATSAPP_FROM"),
        "WHATSAPP_RECIPIENT": os.getenv("WHATSAPP_RECIPIENT"),
    }
    
    all_present = True
    for key, value in credentials.items():
        status = "✅" if value else "❌"
        masked_value = f"{value[:4]}...{value[-4:]}" if value and len(value) > 8 else value
        print(f"{status} {key}: {masked_value}")
        if not value:
            all_present = False
    
    if not all_present:
        print("\n⚠️  Missing credentials!")
        print("📝 Create a .env file with these variables:")
        print("""
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_FROM=+1234567890
WHATSAPP_RECIPIENT=+91XXXXXXXXXX
        """)
        return False
    
    return True


def test_connection():
    """Test connection to Twilio API"""
    print("\n" + "="*60)
    print("🔗 TESTING TWILIO CONNECTION")
    print("="*60)
    
    try:
        whatsapp = initialize_whatsapp()
        status = whatsapp.get_status()
        print(f"✅ {status}")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False


def test_text_alert():
    """Test sending a text-only message"""
    print("\n" + "="*60)
    print("📱 TEST 1: SENDING TEXT-ONLY ALERT")
    print("="*60)
    
    message = """
🧪 *Test Alert - Text Only*

This is a test message to verify WhatsApp integration is working correctly.

✅ If you received this, your Twilio setup is successful!

⏱️ Sent at: 2026-06-10 14:00:00
    """.strip()
    
    print(f"📤 Sending message...")
    print(f"Message:\n{message}\n")
    
    try:
        msg_sid = send_text_alert(message)
        if msg_sid:
            print(f"✅ Message sent successfully!")
            print(f"   Message ID: {msg_sid}")
            print("   Check your WhatsApp in 3-5 seconds...")
            return True
        else:
            print("❌ Failed to send message")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_image_alert():
    """Test sending an alert with image"""
    print("\n" + "="*60)
    print("📷 TEST 2: SENDING ALERT WITH IMAGE")
    print("="*60)
    
    print("📝 Creating test image...")
    
    # Create a test frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add background color
    cv2.rectangle(frame, (0, 0), (640, 480), (40, 100, 200), -1)
    
    # Add title
    cv2.putText(frame, "VigilNet Test Alert", (80, 80),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
    
    # Add student info
    cv2.putText(frame, "Student ID: TEST_001", (120, 180),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, "Risk Score: 75%", (120, 230),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 100, 255), 2)
    cv2.putText(frame, "Status: TALKING", (120, 280),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    
    # Add timestamp
    import datetime
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, f"Time: {ts}", (120, 330),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)
    
    # Add checkmark
    cv2.circle(frame, (500, 380), 40, (0, 255, 0), 3)
    cv2.putText(frame, "✓", (485, 400),
                cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
    
    print("🖼️  Test image created (640x480)")
    print("📤 Sending alert with image...")
    
    event_details = {
        "event_type": "TEST",
        "camera_id": "Camera 1",
        "session_id": "TEST_SESSION",
        "confidence": "95%",
        "description": "Test alert with image - VigilNet WhatsApp Integration"
    }
    
    try:
        msg_sid = send_alert(
            frame,
            student_id=1,
            status="TEST_ALERT",
            risk_score=75,
            attention_score=50,
            event_details=event_details,
            force=True  # Force send even within cooldown
        )
        
        if msg_sid:
            print(f"✅ Alert with image sent successfully!")
            print(f"   Message ID: {msg_sid}")
            print("   Check your WhatsApp in 5-10 seconds...")
            print("   (Images may take longer to load)")
            return True
        else:
            print("❌ Failed to send alert")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  VIGILNET WHATSAPP INTEGRATION TEST SUITE  ".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    results = []
    
    # Test 1: Credentials
    if not test_credentials():
        print("\n❌ Cannot proceed without credentials")
        print("📝 Please set up .env file first")
        return False
    
    results.append(("Credentials", True))
    
    # Test 2: Connection
    if not test_connection():
        print("\n❌ Cannot connect to Twilio")
        print("🔍 Check your credentials and internet connection")
        return False
    
    results.append(("Connection", True))
    
    # Test 3: Text alert
    print("\n💡 TIP: Keep this terminal window open and watch your WhatsApp")
    print("⏱️  You should receive messages within 3-10 seconds")
    
    input("\nPress Enter to send TEXT TEST... ")
    text_ok = test_text_alert()
    results.append(("Text Alert", text_ok))
    
    input("\nPress Enter to send IMAGE TEST... ")
    image_ok = test_image_alert()
    results.append(("Image Alert", image_ok))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\n✅ Your WhatsApp integration is working!")
        print("✅ You can now run: python main.py")
        print("\nAlerts will be automatically sent when violations are detected.")
        return True
    else:
        print("\n" + "="*60)
        print("⚠️  SOME TESTS FAILED")
        print("="*60)
        print("\nPlease check the errors above and try again.")
        print("Common issues:")
        print("  1. Wrong Twilio credentials in .env")
        print("  2. Invalid phone number format (must include +)")
        print("  3. Number not added to WhatsApp sandbox")
        print("  4. No internet connection")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
