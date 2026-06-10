"""
Mobile Alerts & Notifications Module

Sends real-time alerts to mobile devices via Twilio SMS and WhatsApp.
Includes event snapshots, timestamps, confidence scores, and descriptions.
"""

import cv2
import base64
import os
from datetime import datetime
from typing import Optional, Dict, Any
from io import BytesIO

try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("⚠️  Twilio not installed. Install with: pip install twilio")


class MobileAlertManager:
    """Manages mobile notifications via SMS and WhatsApp."""
    
    def __init__(self, 
                 account_sid: Optional[str] = None,
                 auth_token: Optional[str] = None,
                 twilio_phone: Optional[str] = None,
                 recipient_phone: Optional[str] = None,
                 enable_whatsapp: bool = False):
        """
        Initialize mobile alert manager.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            twilio_phone: Twilio phone number
            recipient_phone: Recipient phone number
            enable_whatsapp: Enable WhatsApp notifications
        """
        self.account_sid = account_sid or os.getenv('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = twilio_phone or os.getenv('TWILIO_PHONE')
        self.recipient_phone = recipient_phone or os.getenv('ALERT_PHONE')
        self.enable_whatsapp = enable_whatsapp
        
        self.client = None
        self.alert_history = {}  # Prevent duplicate alerts
        self.alert_cooldown = 30  # seconds between same alerts
        
        if TWILIO_AVAILABLE and all([self.account_sid, self.auth_token, self.twilio_phone]):
            try:
                self.client = Client(self.account_sid, self.auth_token)
                print("✓ Mobile alert system initialized (Twilio)")
            except Exception as e:
                print(f"✗ Failed to initialize Twilio: {e}")
        else:
            print("⚠️  Mobile alerts disabled (missing Twilio credentials)")
    
    def _should_send_alert(self, alert_type: str, student_id: int) -> bool:
        """Check if alert should be sent (cooldown logic)."""
        key = f"{alert_type}_{student_id}"
        now = datetime.now()
        
        if key not in self.alert_history:
            self.alert_history[key] = now
            return True
        
        elapsed = (now - self.alert_history[key]).total_seconds()
        if elapsed >= self.alert_cooldown:
            self.alert_history[key] = now
            return True
        
        return False
    
    def _frame_to_base64(self, frame) -> str:
        """Convert frame to base64 string."""
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')
    
    def _save_alert_image(self, frame, alert_type: str, student_id: int) -> str:
        """Save alert image to violations folder."""
        os.makedirs("violations", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"violations/{alert_type}_S{student_id}_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        return filename
    
    def send_alert(self,
                   frame,
                   student_id: int,
                   alert_type: str,
                   description: str,
                   confidence: float,
                   risk_score: int,
                   proctor_name: str = "System") -> bool:
        """
        Send mobile alert with snapshot and event details.
        
        Args:
            frame: Video frame (BGR image)
            student_id: Student ID
            alert_type: Type of violation (e.g., "TALKING", "LOOKING_AWAY", "PHONE_DETECTED")
            description: Human-readable description
            confidence: Confidence score (0-1)
            risk_score: Overall risk score (0-100)
            proctor_name: Name of proctor
            
        Returns:
            True if alert sent successfully
        """
        if not self.client or not self.recipient_phone:
            return False
        
        # Cooldown check
        if not self._should_send_alert(alert_type, student_id):
            return False
        
        try:
            # Save image
            image_path = self._save_alert_image(frame, alert_type, student_id)
            
            # Compose message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            confidence_pct = int(confidence * 100)
            
            message_text = (
                f"🚨 EXAM PROCTORING ALERT\n"
                f"Student ID: S{student_id}\n"
                f"Event: {alert_type}\n"
                f"Time: {timestamp}\n"
                f"Description: {description}\n"
                f"Confidence: {confidence_pct}%\n"
                f"Risk Score: {risk_score}/100\n"
                f"Proctor: {proctor_name}\n"
                f"Evidence: See attached image"
            )
            
            # Send SMS
            sms_message = self.client.messages.create(
                body=message_text[:160],  # SMS limit
                from_=self.twilio_phone,
                to=self.recipient_phone
            )
            
            print(f"✓ SMS Alert sent (SID: {sms_message.sid})")
            
            # Send WhatsApp with image if enabled
            if self.enable_whatsapp:
                try:
                    whatsapp_message = self.client.messages.create(
                        body=message_text,
                        from_=f"whatsapp:{self.twilio_phone}",
                        to=f"whatsapp:{self.recipient_phone}",
                        media_url=f"file://{os.path.abspath(image_path)}"
                    )
                    print(f"✓ WhatsApp Alert sent (SID: {whatsapp_message.sid})")
                except Exception as e:
                    print(f"⚠️  WhatsApp send failed: {e}")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to send alert: {e}")
            return False
    
    def send_batch_report(self, violations: list, session_id: str) -> bool:
        """
        Send end-of-session batch report with all violations.
        
        Args:
            violations: List of violation dicts
            session_id: Session identifier
            
        Returns:
            True if report sent successfully
        """
        if not self.client or not self.recipient_phone:
            return False
        
        try:
            total_violations = len(violations)
            violation_types = {}
            for v in violations:
                v_type = v.get('type', 'UNKNOWN')
                violation_types[v_type] = violation_types.get(v_type, 0) + 1
            
            summary = "\n".join([f"  • {k}: {v}" for k, v in violation_types.items()])
            
            message = (
                f"📊 SESSION REPORT - {session_id}\n"
                f"Total Violations: {total_violations}\n"
                f"Breakdown:\n{summary}\n"
                f"Check portal for detailed evidence."
            )
            
            self.client.messages.create(
                body=message[:160],
                from_=self.twilio_phone,
                to=self.recipient_phone
            )
            print(f"✓ Batch report sent")
            return True
            
        except Exception as e:
            print(f"✗ Failed to send report: {e}")
            return False


# Fallback system for environments without Twilio
class LocalAlertManager:
    """Local alert system (file-based) when Twilio unavailable."""
    
    def __init__(self):
        self.alert_log_path = "logs/mobile_alerts.log"
        os.makedirs("logs", exist_ok=True)
        self.alert_history = {}
    
    def _should_send_alert(self, alert_type: str, student_id: int) -> bool:
        key = f"{alert_type}_{student_id}"
        now = datetime.now()
        
        if key not in self.alert_history:
            self.alert_history[key] = now
            return True
        
        elapsed = (now - self.alert_history[key]).total_seconds()
        if elapsed >= 30:  # 30 second cooldown
            self.alert_history[key] = now
            return True
        return False
    
    def _save_alert_image(self, frame, alert_type: str, student_id: int) -> str:
        """Save alert image."""
        os.makedirs("violations", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"violations/{alert_type}_S{student_id}_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        return filename
    
    def send_alert(self, frame, student_id: int, alert_type: str,
                   description: str, confidence: float, risk_score: int,
                   proctor_name: str = "System") -> bool:
        """Log alert locally."""
        if not self._should_send_alert(alert_type, student_id):
            return False
        
        try:
            image_path = self._save_alert_image(frame, alert_type, student_id)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            log_entry = (
                f"[{timestamp}] ALERT | S{student_id} | {alert_type} | "
                f"Conf: {int(confidence*100)}% | Risk: {risk_score}/100 | "
                f"Desc: {description} | Image: {image_path}\n"
            )
            
            with open(self.alert_log_path, 'a') as f:
                f.write(log_entry)
            
            print(f"✓ Alert logged locally: {alert_type} - S{student_id}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to log alert: {e}")
            return False
    
    def send_batch_report(self, violations: list, session_id: str) -> bool:
        """Log batch report."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            report = f"\n{'='*60}\nSESSION REPORT - {session_id} [{timestamp}]\n"
            report += f"Total Violations: {len(violations)}\n"
            
            types_count = {}
            for v in violations:
                v_type = v.get('type', 'UNKNOWN')
                types_count[v_type] = types_count.get(v_type, 0) + 1
            
            for v_type, count in sorted(types_count.items()):
                report += f"  • {v_type}: {count}\n"
            report += "="*60 + "\n"
            
            with open(self.alert_log_path, 'a') as f:
                f.write(report)
            
            print(f"✓ Report logged: {session_id}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to log report: {e}")
            return False


def get_alert_manager(use_local: bool = False) -> Any:
    """Factory function to get appropriate alert manager."""
    if use_local or not TWILIO_AVAILABLE:
        return LocalAlertManager()
    return MobileAlertManager()
