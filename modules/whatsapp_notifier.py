"""
WhatsApp Real-Time Notification Module
Sends alerts with images and reports via Twilio WhatsApp API
"""

import os
import cv2
import datetime
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
from twilio.rest import Client

# Load .env from project root (two levels up from this module)
load_dotenv(Path(__file__).parent.parent / ".env")


class WhatsAppNotifier:
    """
    Handles WhatsApp notifications for exam violations.
    Uses Twilio API for reliable real-time delivery.
    """
    
    def __init__(self, account_sid=None, auth_token=None,
                 from_whatsapp=None, to_whatsapp=None):
        """
        Initialize WhatsApp notifier with Twilio credentials.
        
        Args:
            account_sid: Twilio Account SID (or use env var TWILIO_ACCOUNT_SID)
            auth_token: Twilio Auth Token (or use env var TWILIO_AUTH_TOKEN)
            from_whatsapp: Twilio WhatsApp sender number (or env var TWILIO_WHATSAPP_FROM)
            to_whatsapp: Recipient WhatsApp number (or env var WHATSAPP_RECIPIENT)
        """
        self.account_sid = account_sid or os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = auth_token or os.getenv("TWILIO_AUTH_TOKEN")
        self.from_whatsapp = from_whatsapp or os.getenv("TWILIO_WHATSAPP_FROM")
        self.to_whatsapp = to_whatsapp or os.getenv("WHATSAPP_RECIPIENT")
        
        # Initialize Twilio client
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
        else:
            self.client = None
            self.enabled = False
            print("⚠️  WhatsApp notifier disabled: Missing Twilio credentials")
        
        # Cooldown tracking to prevent spam (per student)
        self.notification_cooldown = defaultdict(float)
        self.cooldown_duration = 30  # seconds between alerts per student
        
        # Create temp directory for snapshots
        self.snapshot_dir = Path("violations")
        self.snapshot_dir.mkdir(exist_ok=True)
    
    def set_cooldown(self, duration_seconds):
        """Set the cooldown duration between alerts for the same student."""
        self.cooldown_duration = duration_seconds
    
    def _should_notify(self, student_id):
        """Check if enough time has passed since last notification for this student."""
        current_time = datetime.datetime.now().timestamp()
        last_alert = self.notification_cooldown[student_id]
        
        if current_time - last_alert >= self.cooldown_duration:
            self.notification_cooldown[student_id] = current_time
            return True
        return False
    
    def _save_snapshot(self, frame, student_id, event_type):
        """
        Save a high-quality snapshot from the frame.
        
        Args:
            frame: CV2 frame/image
            student_id: Student identifier
            event_type: Type of violation (e.g., "TALKING", "CHEATING", "OBJECT")
        
        Returns:
            Path to saved snapshot
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        filename = f"violation_S{student_id}_{event_type}_{timestamp}.jpg"
        filepath = self.snapshot_dir / filename
        
        # Save with high quality
        success = cv2.imwrite(
            str(filepath),
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 95]
        )
        
        if success:
            return filepath
        return None

    def _upload_to_public_host(self, file_path):
        """
        Uploads a local image file to a public temporary hosting service.
        Returns the public URL if successful, otherwise None.
        Attempts multiple providers for robustness.
        """
        import requests

        # 1. Try tmpfiles.org
        try:
            url = "https://tmpfiles.org/api/v1/upload"
            with open(file_path, "rb") as f:
                response = requests.post(url, files={"file": f}, timeout=10)
            if response.status_code == 200:
                res_json = response.json()
                viewer_url = res_json.get("data", {}).get("url")
                if viewer_url and "tmpfiles.org/" in viewer_url:
                    # Convert viewer URL to direct download URL
                    return viewer_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        except Exception as e:
            print(f"⚠️ tmpfiles.org upload failed: {e}")

        # 2. Try catbox.moe as fallback
        try:
            url = "https://catbox.moe/user/api.php"
            with open(file_path, "rb") as f:
                response = requests.post(
                    url,
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f},
                    timeout=10
                )
            if response.status_code == 200:
                return response.text.strip()
        except Exception as e:
            print(f"⚠️ catbox.moe upload failed: {e}")

        # 3. Try transfer.sh as final fallback
        try:
            filename = os.path.basename(file_path)
            url = f"https://transfer.sh/{filename}"
            with open(file_path, "rb") as f:
                response = requests.put(url, data=f, timeout=10)
            if response.status_code == 200:
                return response.text.strip()
        except Exception as e:
            print(f"⚠️ transfer.sh upload failed: {e}")

        return None
    
    def _format_report(self, student_id, status, risk_score,
                      attention_score, event_details):
        """
        Format a detailed report message.
        
        Args:
            student_id: Student ID
            status: Current status (e.g., "TALKING!", "LOOKING AWAY")
            risk_score: Risk score 0-100
            attention_score: Attention score 0-100
            event_details: Dict with additional event info
        
        Returns:
            Formatted message string
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Determine severity
        if risk_score >= 70:
            severity = "🔴 CRITICAL"
        elif risk_score >= 40:
            severity = "🟠 HIGH"
        else:
            severity = "🟡 MEDIUM"
        
        # Build message
        report = f"""
*VigilNet Exam Proctoring Alert* {severity}

👤 *Student:* S{student_id}
📅 *Time:* {timestamp}

⚠️ *Violation Detected:*
{status}

📊 *Metrics:*
• Risk Score: {risk_score}% 
• Attention: {attention_score}%
• Confidence: {event_details.get('confidence', 'N/A')}

📍 *Location:* {event_details.get('camera_id', 'Camera 1')}

📝 *Details:*
{event_details.get('description', 'Suspicious activity detected during exam')}

⏱️ Alert ID: {event_details.get('session_id', 'AUTO')}-S{student_id}
        """.strip()
        
        return report
    
    def send_alert(self, frame, student_id, status, risk_score,
                   attention_score, event_details=None, force=False):
        """
        Send a WhatsApp alert with snapshot and report.
        
        Args:
            frame: CV2 frame containing the violation
            student_id: Student ID
            status: Violation status (e.g., "TALKING!", "LOOKING AWAY")
            risk_score: Risk score 0-100
            attention_score: Attention score 0-100
            event_details: Dict with camera_id, session_id, description, confidence
            force: Force send even if within cooldown
        
        Returns:
            Message SID if successful, None otherwise
        """
        if not self.enabled:
            return None
        
        # Check cooldown (unless forced)
        if not force and not self._should_notify(student_id):
            return None
        
        if event_details is None:
            event_details = {}
        
        try:
            # Save snapshot
            snapshot_path = self._save_snapshot(
                frame, student_id, 
                event_details.get('event_type', 'ALERT')
            )
            
            if not snapshot_path or not snapshot_path.exists():
                print(f"❌ Failed to save snapshot for S{student_id}")
                return None
            
            # Format report
            report = self._format_report(
                student_id, status, risk_score,
                attention_score, event_details
            )
            
            # Upload image to public hosting service
            print("📤 Uploading violation snapshot to public host for Twilio access...")
            media_url = self._upload_to_public_host(snapshot_path)
            
            if media_url:
                print(f"✅ Snapshot uploaded: {media_url}")
                # Send via Twilio WhatsApp with image
                message = self.client.messages.create(
                    from_=f"whatsapp:{self.from_whatsapp}",
                    to=f"whatsapp:{self.to_whatsapp}",
                    body=report,
                    media_url=[media_url]  # Attach image
                )
            else:
                print("⚠️ Failed to upload snapshot. Falling back to text-only WhatsApp alert.")
                # Fallback: Send text-only report
                message = self.client.messages.create(
                    from_=f"whatsapp:{self.from_whatsapp}",
                    to=f"whatsapp:{self.to_whatsapp}",
                    body=report + "\n\n*(Snapshot upload failed - text-only alert)*"
                )
            
            print(f"✅ WhatsApp alert sent to {self.to_whatsapp} "
                  f"(S{student_id}, SID: {message.sid})")
            
            return message.sid
        
        except Exception as e:
            print(f"❌ Failed to send WhatsApp alert: {str(e)}")
            return None
    
    def send_text_alert(self, message_text):
        """
        Send a simple text-only alert (no image).
        
        Args:
            message_text: Alert message text
        
        Returns:
            Message SID if successful, None otherwise
        """
        if not self.enabled:
            return None
        
        try:
            message = self.client.messages.create(
                from_=f"whatsapp:{self.from_whatsapp}",
                to=f"whatsapp:{self.to_whatsapp}",
                body=message_text
            )
            print(f"✅ WhatsApp text alert sent (SID: {message.sid})")
            return message.sid
        except Exception as e:
            print(f"❌ Failed to send text alert: {str(e)}")
            return None
    
    def get_status(self):
        """Get current notifier status."""
        if self.enabled:
            return (f"✅ Enabled | Recipient: {self.to_whatsapp} | "
                    f"Cooldown: {self.cooldown_duration}s")
        else:
            return "❌ Disabled - Configure Twilio credentials"


# Global instance
_notifier = None


def initialize_whatsapp(account_sid=None, auth_token=None,
                        from_whatsapp=None, to_whatsapp=None):
    """Initialize the global WhatsApp notifier."""
    global _notifier
    _notifier = WhatsAppNotifier(
        account_sid, auth_token,
        from_whatsapp, to_whatsapp
    )
    return _notifier


def send_alert(frame, student_id, status, risk_score,
               attention_score, event_details=None, force=False):
    """Send an alert using the global notifier."""
    if _notifier is None:
        initialize_whatsapp()
    return _notifier.send_alert(
        frame, student_id, status, risk_score,
        attention_score, event_details, force
    )


def send_text_alert(message_text):
    """Send a text-only alert using the global notifier."""
    if _notifier is None:
        initialize_whatsapp()
    return _notifier.send_text_alert(message_text)


def get_notifier():
    """Get the global notifier instance."""
    if _notifier is None:
        initialize_whatsapp()
    return _notifier
