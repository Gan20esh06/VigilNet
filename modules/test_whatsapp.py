from whatsapp_notifier import initialize_whatsapp, send_text_alert
import cv2
import numpy as np

# Initialize
whatsapp = initialize_whatsapp()
print(whatsapp.get_status())

# Test 1: Send text-only alert
send_text_alert("🧪 Test: WhatsApp integration working!")

# Test 2: Send alert with image
# Create a test frame
test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
cv2.putText(test_frame, "Test Alert Frame", (100, 240),
            cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

from whatsapp_notifier import send_alert
send_alert(
    test_frame,
    student_id=1,
    status="TEST_ALERT",
    risk_score=75,
    attention_score=50,
    event_details={
        "event_type": "TEST",
        "camera_id": "Test Camera",
        "session_id": "test_session",
        "confidence": "95%",
        "description": "This is a test alert from VigilNet"
    },
    force=True  # Force send even within cooldown
)