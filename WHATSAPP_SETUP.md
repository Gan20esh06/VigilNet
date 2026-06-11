# VigilNet WhatsApp Real-Time Alerts Setup Guide

## 🚀 Quick Start

This guide explains how to set up **real-time WhatsApp notifications** for your exam proctoring system using **Twilio**.

---

## 📋 Prerequisites

1. **Python 3.8+** (already installed)
2. **Twilio Account** (free trial available)
3. **WhatsApp** - Either personal or business account
4. Active internet connection

---

## Step 1: Create a Twilio Account

### 1.1 Sign Up (Free)

- Visit: https://www.twilio.com/try-twilio
- Sign up with your email
- Verify your email and phone number
- Create a free trial account (includes $15 credit)

### 1.2 Get Your Credentials

After logging in to Twilio Console:

1. Go to **Account Info** (top-left dropdown)
2. Copy your **Account SID** - looks like: `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
3. Copy your **Auth Token** - looks like: `your_token_here`
4. Keep these safe! Never share them.

---

## Step 2: Set Up WhatsApp Messaging (Sandbox Mode - Fastest)

### 2.1 Access WhatsApp Sandbox

1. In Twilio Console, navigate: **Messaging → WhatsApp → Sandbox Settings**
2. You'll see a **Sandbox Phone Number** - note this down (looks like: `+1234567890`)

### 2.2 Add Your Number to Sandbox

1. Send this exact message from your WhatsApp to the sandbox number:
   ```
   join YOUR-SANDBOX-CODE
   ```
   (Example: `join clever-octopus`)
2. You'll receive confirmation - you're now connected!

### 2.3 Note Your Phone Number

- Have the **recipient phone number** ready (the number where you'll receive alerts)
- Format: `+[country_code][phone_number]`
- Example: `+91XXXXXXXXXX` (for India)

---

## Step 3: Production Setup (Optional - For Permanent Deployment)

If you want to use WhatsApp without sandbox limitations:

### 3.1 Register WhatsApp Business Account

1. Contact Twilio sales or go to: **Messaging → WhatsApp → Sender Pools**
2. Complete WhatsApp Business verification (requires business documentation)
3. Get your **Production Phone Number**

### 3.2 Benefits of Production

- No daily message limits
- Persistent phone number
- Professional appearance with verified badge
- Support for templates and bulk messaging

---

## Step 4: Configure Environment Variables

### 4.1 Create `.env` File

Create a `.env` file in the `d:\exam_proctor` directory:

```env
# Twilio Credentials
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=+1234567890
WHATSAPP_RECIPIENT=+91XXXXXXXXXX
```

### 4.2 Fill in Your Values

Replace with actual values from Twilio:

- `TWILIO_ACCOUNT_SID`: Your Account SID
- `TWILIO_AUTH_TOKEN`: Your Auth Token
- `TWILIO_WHATSAPP_FROM`: Sandbox phone number (or your production number)
- `WHATSAPP_RECIPIENT`: Your personal WhatsApp number

### 4.3 Secure Your Credentials

```bash
# Add to .gitignore to prevent accidentally pushing credentials
echo ".env" >> .gitignore
```

---

## Step 5: Install Dependencies

### 5.1 Update Dependencies

```bash
pip install -r requirements.txt
```

This installs:

- `twilio` - WhatsApp API client
- `python-dotenv` - Environment variable loader

### 5.2 Verify Installation

```bash
python -c "from twilio.rest import Client; print('✅ Twilio installed successfully')"
```

---

## Step 6: Test the System

### 6.1 Manual Test (Optional)

Create a test script `test_whatsapp.py`:

```python
from modules.whatsapp_notifier import initialize_whatsapp, send_text_alert
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

from modules.whatsapp_notifier import send_alert
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
```

Run it:

```bash
python test_whatsapp.py
```

You should receive a WhatsApp message within seconds!

---

## Step 7: Run the Exam Proctor with WhatsApp Alerts

### 7.1 Start the System

```bash
python main.py
```

### 7.2 What Happens

✅ System initializes  
✅ WhatsApp notifier connects to Twilio  
✅ When a violation is detected:

- High-quality snapshot is captured
- Detailed report is formatted
- Image + report sent to your WhatsApp instantly
- Alert appears on your phone with:
  - Student ID
  - Violation type (TALKING, LOOKING AWAY, OBJECT)
  - Risk score & Attention score
  - Timestamp
  - Camera location
  - Snapshot image

---

## 📊 Alert Message Format Example

You'll receive messages like:

```
*VigilNet Exam Proctoring Alert* 🔴 CRITICAL

👤 *Student:* S1
📅 *Time:* 2026-06-10 14:30:45

⚠️ *Violation Detected:*
TALKING!

📊 *Metrics:*
• Risk Score: 82%
• Attention: 25%
• Confidence: 82%

📍 *Location:* Camera 1

📝 *Details:*
Student 1 detected: TALKING!
Attention Score: 25%
Risk Assessment: 82%

⏱️ Alert ID: 20260610_143045-S1

[+ Snapshot Image Attached]
```

---

## 🎯 Configuration Options

### Adjust Alert Cooldown

By default, you get **one alert per student per 30 seconds** to avoid spam.

Edit in `main.py`:

```python
whatsapp.set_cooldown(60)  # Change to 60 seconds
```

### Modify Recipient

To send alerts to multiple people, modify the module to loop through a list:

In `modules/whatsapp_notifier.py`:

```python
RECIPIENTS = [
    "+91XXXXXXXXXX",  # Proctor 1
    "+91YYYYYYYYYY",  # Proctor 2
]
```

### Customize Alert Message

Edit the `_format_report()` method in `modules/whatsapp_notifier.py` to change message format.

---

## 🔧 Troubleshooting

### ❌ "WhatsApp notifier disabled: Missing Twilio credentials"

**Solution:** Check your `.env` file exists in `d:\exam_proctor` with all 4 values filled in.

### ❌ "Failed to send WhatsApp alert: 21608"

**Error:** Message not sent within sandbox limits.
**Solution:** Your number isn't added to sandbox. Resend the "join [code]" message.

### ❌ "Failed to send WhatsApp alert: 21405"

**Error:** Invalid phone number format.
**Solution:** Ensure numbers start with `+` and include country code. Example: `+919876543210`

### ❌ No message received after 5 minutes

**Possible Issues:**

1. Check Twilio account has remaining trial credits
2. Verify phone numbers are correct
3. Check internet connection
4. Restart the system

### ✅ Check Message Status

In Twilio Console → **Logs → Messages** to see delivery status

---

## 📈 Scaling to Production

### Moving from Sandbox to Production

1. Get WhatsApp Business Account verification
2. Update `.env` with production phone numbers
3. No code changes needed - system uses environment variables
4. Deploy as-is

### Using AWS/Cloud

```python
# The notifier is cloud-ready:
# 1. Store .env in secrets manager (AWS Secrets Manager, Azure Key Vault)
# 2. Update .env loading to fetch from there
# 3. Deploy with container/serverless
```

---

## 💡 Best Practices

✅ **DO:**

- Use production WhatsApp after testing
- Monitor Twilio dashboard for usage
- Keep cooldown between 20-60 seconds
- Test thoroughly before exam day
- Backup credentials securely

❌ **DON'T:**

- Share Twilio credentials publicly
- Commit `.env` to Git
- Use invalid phone numbers
- Change credentials during session
- Over-configure alerts (will cause spam)

---

## 📞 Support

- **Twilio Docs:** https://www.twilio.com/docs/whatsapp
- **WhatsApp Business API:** https://www.whatsapp.com/business/api/
- **Twilio Console:** https://console.twilio.com
- **Contact Twilio:** support@twilio.com

---

## 🎉 You're All Set!

Your VigilNet exam proctoring system now has **enterprise-grade WhatsApp real-time alerts**. Students getting caught cheating will know you're watching instantly! 👀

**Next Steps:**

1. ✅ Create Twilio account
2. ✅ Set up WhatsApp sandbox
3. ✅ Create `.env` file with credentials
4. ✅ Run `pip install -r requirements.txt`
5. ✅ Test with `test_whatsapp.py`
6. ✅ Start system: `python main.py`

Happy proctoring! 📚
