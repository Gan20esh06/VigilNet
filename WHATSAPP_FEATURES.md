# VigilNet — Real-Time WhatsApp Alerts

## 🎯 Overview

VigilNet now includes **enterprise-grade WhatsApp real-time notifications** that instantly alert you whenever suspicious activity is detected during an exam. Each alert includes:

- 📸 **High-quality snapshot** of the detected violation
- ⏰ **Timestamp** of when the event occurred
- 📊 **Risk & Attention scores** showing severity levels
- 👤 **Student identification** (ID and location)
- 📝 **Detailed report** describing the violation
- 🎯 **Confidence metrics** showing detection accuracy

---

## 🚀 Quick Setup (5 minutes)

### 1️⃣ Create Twilio Account

Go to https://www.twilio.com/try-twilio and sign up (free account with $15 credit)

### 2️⃣ Get WhatsApp Sandbox Access

1. Log into Twilio Console
2. Go to **Messaging → WhatsApp → Sandbox Settings**
3. Note the sandbox phone number and code
4. Send from WhatsApp: `join [YOUR-SANDBOX-CODE]`

### 3️⃣ Create `.env` File

Copy `.env.template` to `.env` and fill in:

```env
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=your_token...
TWILIO_WHATSAPP_FROM=+1234567890
WHATSAPP_RECIPIENT=+91XXXXXXXXXX
```

### 4️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 5️⃣ Test It

```bash
python test_whatsapp_integration.py
```

### 6️⃣ Run the System

```bash
python main.py
```

That's it! You'll now receive WhatsApp alerts instantly. 🎉

---

## 📱 What You'll Receive

When a violation is detected, you'll get a WhatsApp message with:

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

[+ High-quality snapshot image]
```

---

## ⚙️ Configuration

### Alert Cooldown

By default, one alert per student per **30 seconds** (prevents spam).

To change in `main.py`:

```python
whatsapp.set_cooldown(60)  # Change to 60 seconds
```

### Multiple Recipients

To notify multiple people, update `modules/whatsapp_notifier.py`:

```python
RECIPIENTS = [
    "+91PROCTOR1",
    "+91PROCTOR2",
    "+91ADMIN"
]
```

### Custom Message Format

Edit `_format_report()` in `modules/whatsapp_notifier.py` to customize alert appearance.

---

## 🔧 Technical Details

### Architecture

```
Violation Detected (main.py)
         ↓
    Event Data Captured
         ↓
  Frame Snapshot Saved
         ↓
  Report Formatted
         ↓
WhatsApp Notifier Module
         ↓
  Twilio API Call
         ↓
WhatsApp Message Sent
         ↓
Recipient Receives Alert (3-5 seconds)
```

### Key Features

✅ **Real-time**: Alerts sent instantly (no batching/delays)  
✅ **Reliable**: Twilio handles delivery, retries, confirmations  
✅ **Scalable**: Works with 1 or 100+ students  
✅ **Secure**: Credentials stored in .env (excluded from Git)  
✅ **Async**: Non-blocking alerts (doesn't interrupt video processing)  
✅ **Smart**: One alert per student per 30s (prevents notification spam)

### Module Details

**`modules/whatsapp_notifier.py`:**

- `WhatsAppNotifier` class: Main notification engine
- Twilio client initialization
- Frame snapshot capture (95% JPEG quality)
- Report formatting with rich emoji indicators
- Cooldown tracking per student
- Error handling & retry logic

**Integration in `main.py`:**

- Imports WhatsApp notifier
- Initializes Twilio on startup
- Sends alert when violation confirmed
- Includes snapshot, risk scores, and detailed description

---

## 📊 Violation Types & Alerts

### Type 1: TALKING

- **Detection**: Audio + Lip movement combined
- **Alert**: "TALKING!" with mouth close-up
- **Risk**: High (75%+)

### Type 2: LOOKING AWAY

- **Detection**: Head pose deviation from screen
- **Alert**: "LOOKING AWAY" with head position
- **Risk**: Medium (40-70%)

### Type 3: SUSPICIOUS OBJECTS

- **Detection**: Cell phone, unauthorized materials detected
- **Alert**: "OBJECT:[NAME]" with bounding box
- **Risk**: Critical (80%+)

### Type 4: NO FACE

- **Detection**: Student left frame or face obscured
- **Alert**: "NO FACE" warning
- **Risk**: High (70%+)

---

## 🛡️ Security & Privacy

✅ **Credentials protected**: .env file in .gitignore  
✅ **No face storage**: Images only stored temporarily, deleted after send  
✅ **HTTPS encryption**: Twilio uses TLS for all communications  
✅ **Audit trail**: Message IDs logged for compliance  
✅ **Rate limiting**: Built-in cooldown prevents abuse

### Best Practices

1. **Keep .env private** - Never commit to Git
2. **Rotate tokens periodically** - Update Twilio credentials monthly
3. **Monitor usage** - Check Twilio dashboard for anomalies
4. **Test before deployment** - Run test script first
5. **Secure backups** - Store credentials in vault, not files

---

## 🧪 Testing

### Quick Test

```bash
python test_whatsapp_integration.py
```

This will:

1. Verify Twilio credentials
2. Test API connection
3. Send sample text alert
4. Send sample alert with image
5. Show delivery status

### Manual Test

```python
from modules.whatsapp_notifier import send_text_alert

send_text_alert("🧪 Testing WhatsApp integration!")
```

---

## 🐛 Troubleshooting

| Issue                        | Cause                         | Solution                       |
| ---------------------------- | ----------------------------- | ------------------------------ |
| "Missing Twilio credentials" | .env file missing or empty    | Create .env from .env.template |
| "21608 error"                | Number not in sandbox         | Send "join [code]" to sandbox  |
| "21405 error"                | Invalid phone format          | Use +[country_code][number]    |
| No message received          | Twilio account out of credits | Check Twilio account balance   |
| Image not loading            | Image file too large          | System uses 95% JPEG quality   |
| Alerts not sending           | System crash/restart          | Check console for errors       |

---

## 📈 Scaling to Production

### Move to Production WhatsApp

1. Contact Twilio sales for WhatsApp Business account
2. Complete business verification
3. Update .env with production phone numbers
4. System works unchanged - same code!

### Cloud Deployment

```bash
# AWS Lambda / Azure Functions / Google Cloud Run
1. Store .env in Secrets Manager
2. Deploy whatsapp_notifier.py as serverless function
3. Call from main.py via API
```

---

## 📞 Support

- **Setup Guide**: See `WHATSAPP_SETUP.md`
- **Test Tool**: Run `python test_whatsapp_integration.py`
- **Twilio Docs**: https://www.twilio.com/docs/whatsapp
- **Issues**: Check Twilio Console → Logs → Messages

---

## 🎓 How It Works Behind the Scenes

1. **Detection Loop** runs at ~30 FPS
2. When violation detected → Image captured from current frame
3. **Confidence check** ensures not false positive (4+ frames confirmation)
4. **Cooldown check** (30 sec per student) prevents spam
5. **Snapshot saved** to `/violations/` with timestamp
6. **Report formatted** with rich metadata
7. **Twilio API called** with image + text
8. **Message queued** for delivery
9. **Status returned** with Message SID
10. **Alert logged** to violation records

---

## ✨ Example Use Cases

### 👨‍🏫 Proctor Scenario

- Exam starts, system armed
- Student tries to talk → Instant WhatsApp alert
- Proctor sees snapshot + risk score in 3 seconds
- Can immediately intervene or collect evidence
- All incidents logged with images for records

### 🏆 High-Stakes Exams

- Multiple proctors monitoring
- Alerts go to all responsible staff
- Tamper-proof image evidence
- Compliance audit trail

### 📱 Remote Proctoring

- Proctor on different location
- Gets real-time alerts on phone
- Can share with other staff instantly
- Works even with poor WiFi (Twilio handles retries)

---

## 🎉 You're All Set!

Your VigilNet system now has enterprise-grade WhatsApp alerts. Students are no longer invisible during exams—you get instant notifications the moment they break rules.

**Next time a student tries to cheat, they'll learn that VigilNet watches 24/7.** 👀

---

**Questions?** Check `WHATSAPP_SETUP.md` for detailed step-by-step instructions.

**Ready to run?** Execute: `python main.py` and watch the alerts flow in! 📲
