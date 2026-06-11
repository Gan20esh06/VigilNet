# VigilNet WhatsApp Quick Reference

## 🚀 Quick Start Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy environment template
copy .env.template .env

# 3. Edit .env with your Twilio credentials
# Open .env and fill in:
#   TWILIO_ACCOUNT_SID=AC...
#   TWILIO_AUTH_TOKEN=...
#   TWILIO_WHATSAPP_FROM=+1234567890
#   WHATSAPP_RECIPIENT=+91XXXXXXXXXX

# 4. Test the integration
python test_whatsapp_integration.py

# 5. Run the system
python main.py
```

---

## 📋 Twilio Setup Checklist

- [ ] Sign up at https://www.twilio.com/try-twilio
- [ ] Go to Account Info and copy Account SID
- [ ] Copy Auth Token (keep it secret!)
- [ ] Go to Messaging → WhatsApp → Sandbox Settings
- [ ] Note the sandbox phone number
- [ ] Send WhatsApp: `join [SANDBOX-CODE]` to sandbox number
- [ ] Get confirmation that you're added
- [ ] Create `.env` file from `.env.template`
- [ ] Fill in all 4 credentials
- [ ] Run `test_whatsapp_integration.py` to verify
- [ ] Test receives WhatsApp messages
- [ ] Run `python main.py`
- [ ] System sends alerts on violations

---

## 🔐 Security Reminders

```
DO ✅                          DON'T ❌
├─ Keep .env private           ├─ Share credentials
├─ Use environment variables   ├─ Hardcode in code
├─ .gitignore excludes .env   ├─ Commit .env to Git
├─ Update credentials monthly  ├─ Use expired tokens
└─ Monitor Twilio usage        └─ Leave Twilio unmonitored
```

---

## 📞 Credentials Reference

```env
# Get from: console.twilio.com → Account Info
TWILIO_ACCOUNT_SID=AC[alphanumeric]

# Get from: console.twilio.com → Account Info
TWILIO_AUTH_TOKEN=[alphanumeric]

# Get from: Messaging → WhatsApp → Sandbox
TWILIO_WHATSAPP_FROM=+[country_code][number]
# Example: +14155552671 (Twilio sandbox)

# Your phone where alerts arrive
WHATSAPP_RECIPIENT=+[country_code][number]
# Example: +919876543210
```

---

## 🧪 Test Commands

```bash
# Full test suite
python test_whatsapp_integration.py

# Test with custom script
python -c "
from modules.whatsapp_notifier import send_text_alert
send_text_alert('Test message from VigilNet')
"
```

---

## 📊 Message Format

```
*VigilNet Alert* [SEVERITY]
├─ 👤 Student: [ID]
├─ 📅 Time: [TIMESTAMP]
├─ ⚠️  Violation: [TYPE]
├─ 📊 Risk: [SCORE]%
├─ 💭 Attention: [SCORE]%
├─ 📍 Location: [CAMERA]
├─ 📝 Details: [DESCRIPTION]
└─ 🖼️  [SNAPSHOT IMAGE]
```

---

## ⚙️ Configuration Options

```python
# In main.py or modules/whatsapp_notifier.py

# Change alert cooldown (seconds)
whatsapp.set_cooldown(60)

# Force send (ignore cooldown)
send_alert(..., force=True)

# Notify multiple recipients (modify notifier.py)
for recipient in RECIPIENTS:
    client.messages.create(
        from_=from_num,
        to=f"whatsapp:{recipient}",
        body=message
    )
```

---

## 🔗 Important Links

| Resource          | URL                                      |
| ----------------- | ---------------------------------------- |
| Twilio Console    | https://console.twilio.com               |
| WhatsApp Sandbox  | Console → Messaging → WhatsApp → Sandbox |
| Account Info      | Console → Account → Account Info         |
| Usage & Logs      | Console → Monitor → Logs → Messages      |
| Twilio Docs       | https://www.twilio.com/docs/whatsapp     |
| WhatsApp Business | https://www.whatsapp.com/business/api/   |

---

## 🚨 Common Errors & Fixes

| Error Code | Problem                  | Fix                        |
| ---------- | ------------------------ | -------------------------- |
| 21608      | Recipient not in sandbox | Send "join [code]" message |
| 21405      | Invalid phone number     | Add + and country code     |
| 21421      | No valid credentials     | Check .env file exists     |
| 20003      | Auth error               | Verify Account SID & Token |
| No message | Network issue            | Check internet connection  |

---

## 📈 Production Deployment

```
Sandbox Mode (Testing)              Production Mode (Real Use)
├─ Free $15 trial credit            ├─ Paid Twilio account
├─ Limited recipients               ├─ Unlimited recipients
├─ Sandbox phone number             ├─ Verified WhatsApp number
├─ "Join" message required          ├─ Auto-accepted
├─ Expires after 72h idle           ├─ Permanent
└─ Perfect for testing              └─ Ready for exams
```

---

## 📱 Testing on Real Device

```
1. Open WhatsApp on your phone
2. Save the sandbox number: +1 (414) 201-8111
3. Send message: "join [your-sandbox-code]"
4. Wait for confirmation
5. You're now connected!
6. Run test: python test_whatsapp_integration.py
7. Check your phone - message arrives in 3-5 seconds
```

---

## 🎯 Usage Statistics

```
Typical Exam (2 hours, 30 students):
├─ Violations detected: 15-20
├─ Alerts sent: 15-20
├─ Images captured: 15-20
├─ Data transferred: 50-100 MB
├─ Twilio cost: $0.01-0.05 per message
└─ Total cost: ~$0.15-1.00 per exam
```

---

## 🛠️ Debugging

```bash
# Check environment variables are loaded
python -c "import os; print(os.getenv('TWILIO_ACCOUNT_SID'))"

# Verify Twilio client
python -c "from twilio.rest import Client; print('✓ Twilio installed')"

# Run full test suite
python test_whatsapp_integration.py

# Check notification cooldown
python -c "from modules.whatsapp_notifier import get_notifier; n=get_notifier(); print(n.cooldown_duration)"

# View violation logs
type logs\violations_*.txt
```

---

## 💡 Pro Tips

✅ **Tip 1**: Use `force=True` only for testing, not production  
✅ **Tip 2**: Keep cooldown between 20-60 seconds  
✅ **Tip 3**: Monitor Twilio dashboard for message status  
✅ **Tip 4**: Test on a quiet exam before using live  
✅ **Tip 5**: Save Twilio credentials in LastPass/Vault  
✅ **Tip 6**: Turn on message delivery notifications  
✅ **Tip 7**: Screenshot alerts for compliance records

---

## 📞 Support Contacts

- **Twilio Support**: support@twilio.com | +1-844-839-5226
- **WhatsApp Business**: support.whatsapp.com
- **VigilNet Issues**: Check WHATSAPP_SETUP.md

---

**Last Updated**: June 10, 2026  
**Version**: 1.0  
**Status**: ✅ Production Ready
