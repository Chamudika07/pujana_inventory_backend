# Quick Reference - Low Stock Alert System

## 📱 API Quick Commands

### 1. Update User Preferences (Setup)
```bash
curl -X PUT "http://localhost:8000/alerts/preferences/update" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+919876543210",
    "notification_email": "alerts@example.com",
    "notification_enabled": true,
    "alert_threshold": 5
  }'
```

### 2. Get Your Preferences
```bash
curl -X GET "http://localhost:8000/alerts/preferences/get" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Get All Alerts
```bash
curl -X GET "http://localhost:8000/alerts/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Get Alert Stats
```bash
curl -X GET "http://localhost:8000/alerts/stats" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. Update Item Quantity (Triggers Alert if < threshold)
```bash
curl -X PUT "http://localhost:8000/items/5" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Resistor 1K",
    "quantity": 3,
    "buying_price": 0.50,
    "selling_price": 1.00,
    "description": "1K Ohm Resistor",
    "model_number": "RES-1K",
    "category_id": 1
  }'
```

### 6. Resolve Alert
```bash
curl -X PUT "http://localhost:8000/alerts/1/resolve" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 7. Manually Trigger Low Stock Check
```bash
curl -X POST "http://localhost:8000/alerts/trigger-check" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔧 Configuration Checklist

```
.env File Setup:
├─ DATABASE_HOSTNAME=localhost
├─ DATABASE_PORT=5432
├─ DATABASE_USERNAME=postgres
├─ DATABASE_PASSWORD=your_password
├─ DATABASE_NAME=pujana_inventory
├─ SMTP_SERVER=smtp.gmail.com
├─ SMTP_PORT=587
├─ EMAIL_SENDER=your_email@gmail.com
├─ EMAIL_PASSWORD=your_app_password
├─ TWILIO_ACCOUNT_SID=optional
├─ TWILIO_AUTH_TOKEN=optional
└─ TWILIO_WHATSAPP_NUMBER=optional
```

---

## 📊 System Flow

```
┌─────────────────────────────────┐
│  User Updates Item Quantity     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│ Check: quantity < threshold?    │
└────────────┬────────────────────┘
             │
        YES  │  NO
             ▼
┌─────────────────────────────────┐
│ Create/Update Alert Record      │
└────────────┬────────────────────┘
             │
             ▼
    ┌────────┴────────┐
    ▼                 ▼
┌────────────┐  ┌──────────────┐
│Send Email  │  │Send WhatsApp │
└────────────┘  └──────────────┘
```

---

## ⏰ Daily Scheduler

```
Every Day at 9:00 AM UTC:

1. Check all unresolved alerts
2. For each alert:
   - Is item still low stock? YES → Check 24 hours passed?
   - YES → Send reminder + Update timestamps
   - NO → Mark as resolved
3. Done!
```

---

## 🎯 Test Flow (Step by Step)

**Step 1:** Set up preferences
```
PUT /alerts/preferences/update
  phone: +919876543210
  email: test@gmail.com
  threshold: 5
```

**Step 2:** Create item with quantity 100
```
POST /items/
  name: LED Red
  quantity: 100
```

**Step 3:** Update quantity to 3 (triggers alert!)
```
PUT /items/1
  quantity: 3
```

**Step 4:** ✅ Check your email and WhatsApp

**Step 5:** View your alerts
```
GET /alerts/
```

**Step 6:** Restock and resolve
```
PUT /items/1
  quantity: 50

PUT /alerts/1/resolve
```

---

## 🐛 Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Email not sending | Gmail credentials wrong | Use App Password, not regular password |
| WhatsApp not sending | Twilio not configured | Optional - set TWILIO_* in .env or ignore |
| No alert created | Quantity >= threshold | Update quantity to below threshold |
| Duplicate alerts | Scheduler running twice | Restart server once |
| Database error | Migration not run | Run: `alembic upgrade head` |

---

## 📝 File Structure

```
✅ Created Files:
├── app/models/low_stock_alert.py
├── app/services/notification_service.py
├── app/services/alert_service.py
├── app/services/scheduler.py
├── app/routers/alert.py
├── app/schemas/low_stock_alert.py
├── .env.example
├── LOW_STOCK_ALERT_SYSTEM.md
└── QUICK_REFERENCE.md (this file)

✅ Modified Files:
├── app/models/user.py (added fields)
├── app/models/item.py (added relationship)
├── app/routers/item.py (added alert trigger)
├── app/main.py (added scheduler)
└── requirements.txt (added packages)
```

---

## 🚀 Deployment Tips

1. **Production Email:** Use SendGrid or AWS SES instead of Gmail
2. **Production WhatsApp:** Get production Twilio account (not trial)
3. **Timezone:** Change `hour=9` in scheduler.py to match your timezone
4. **Logging:** Set up centralized logging (ELK, DataDog, etc.)
5. **Monitoring:** Monitor scheduler job execution and failures

---

## 💡 Next Steps (Optional)

- [ ] SMS support (non-WhatsApp)
- [ ] Slack notifications
- [ ] Webhook notifications
- [ ] Batch email digest (all items in one email)
- [ ] Alert escalation (urgent if < 3 items)
- [ ] User dashboard (view all their low stock items)
- [ ] Admin dashboard (view all alerts across users)
- [ ] Mobile app notifications

---

## 📞 Debug Commands

### Check Scheduler Status
```bash
# Look for these logs on startup:
# "✅ Scheduler started successfully"
# "🔍 Starting daily low stock check..."
```

### Manual Database Query
```sql
-- Check alerts for a user
SELECT * FROM low_stock_alerts WHERE user_id = 1;

-- Check user preferences
SELECT phone_number, notification_email, alert_threshold 
FROM users WHERE id = 1;

-- Check low stock items
SELECT * FROM items WHERE quantity < 5;
```

### Python Testing
```python
from app.services.alert_service import AlertService
from app.database import SessionLocal

db = SessionLocal()

# Test alert creation
AlertService.check_and_create_alert(
    db=db,
    item_id=1,
    user_id=1,
    current_quantity=3,
    alert_threshold=5
)

db.close()
```

---

Good Luck! 🎉
