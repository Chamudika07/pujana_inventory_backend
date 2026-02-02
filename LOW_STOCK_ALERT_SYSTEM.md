# Low Stock Alert System - Complete Documentation

## 📋 Overview

This system automatically monitors inventory levels and sends notifications (Email & WhatsApp) when items fall below a configured threshold. It includes:

- ✅ Real-time alert creation when quantity drops below threshold
- ✅ Daily automated reminder checks
- ✅ Email notifications with HTML templates
- ✅ WhatsApp/SMS notifications via Twilio
- ✅ User preferences management
- ✅ Alert history and statistics
- ✅ 24-hour spam prevention (won't send duplicate alerts within 24 hours)

---

## 🗂️ Project Structure

```
app/
├── models/
│   ├── low_stock_alert.py      # LowStockAlert database model
│   ├── user.py                 # Updated User model (new fields)
│   └── item.py                 # Updated Item model (relationships)
├── services/
│   ├── notification_service.py # Email & WhatsApp sending logic
│   ├── alert_service.py        # Alert creation and management
│   └── scheduler.py            # Automated daily checks
├── routers/
│   ├── alert.py                # Alert management endpoints
│   └── item.py                 # Updated with alert triggers
├── schemas/
│   └── low_stock_alert.py      # Pydantic models for validation
└── main.py                      # Updated with scheduler startup
```

---

## 🔧 Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```
# Database (existing)
DATABASE_HOSTNAME=localhost
DATABASE_PORT=5432
DATABASE_USERNAME=postgres
DATABASE_PASSWORD=your_password
DATABASE_NAME=pujana_inventory

# Email Configuration (Gmail)
EMAIL_SENDER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # Use Gmail App Passwords!

# Twilio Configuration (optional, for WhatsApp)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+14155552671
```

#### Setting Up Gmail App Password:
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-factor authentication
3. Create an "App Password" for "Mail" on Windows or macOS
4. Use this 16-character password in `.env`

#### Setting Up Twilio (Optional):
1. Create account at [Twilio](https://www.twilio.com)
2. Get trial WhatsApp number
3. Add your phone number to Twilio console
4. Copy credentials to `.env`

### 3. Run Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "low_stock_alerts"

# Run migration
alembic upgrade head
```

Or use the provided migration:
```bash
alembic upgrade +1
```

### 4. Start the Server
```bash
uvicorn app.main:app --reload
```

---

## 📡 API Endpoints

### Alert Management

#### Get User's Alerts
```http
GET /alerts/
Authorization: Bearer {token}
```

Query Parameters:
- `show_resolved` (boolean): Show resolved alerts (default: false)

Response:
```json
[
  {
    "id": 1,
    "item_id": 5,
    "user_id": 1,
    "quantity_at_alert": 3,
    "alert_type": "BOTH",
    "is_resolved": false,
    "created_at": "2024-02-02T10:00:00",
    "last_sent_at": "2024-02-02T10:01:00",
    "next_alert_at": "2024-02-03T10:01:00",
    "item": {...}
  }
]
```

---

#### Get Alert Statistics
```http
GET /alerts/stats
Authorization: Bearer {token}
```

Response:
```json
{
  "total_alerts": 10,
  "active_alerts": 3,
  "resolved_alerts": 7,
  "low_stock_items": 5
}
```

---

#### Get Specific Alert
```http
GET /alerts/{alert_id}
Authorization: Bearer {token}
```

---

#### Resolve Alert (Mark Item as Restocked)
```http
PUT /alerts/{alert_id}/resolve
Authorization: Bearer {token}
```

Response: Updated alert object with `is_resolved: true`

---

#### Update User Preferences
```http
PUT /alerts/preferences/update
Authorization: Bearer {token}
Content-Type: application/json

{
  "phone_number": "+919876543210",
  "notification_email": "alerts@example.com",
  "notification_enabled": true,
  "alert_threshold": 5
}
```

Response:
```json
{
  "message": "Preferences updated successfully",
  "phone_number": "+919876543210",
  "notification_email": "alerts@example.com",
  "notification_enabled": true,
  "alert_threshold": 5
}
```

---

#### Get User Preferences
```http
GET /alerts/preferences/get
Authorization: Bearer {token}
```

---

#### Manually Trigger Low Stock Check
```http
POST /alerts/trigger-check
Authorization: Bearer {token}
```

Response:
```json
{
  "message": "Low stock check completed",
  "items_checked": 15,
  "alerts_sent": 3
}
```

---

## 🔄 How It Works

### 1. Real-Time Alert (When Updating Item Quantity)

**Flow:**
```
User updates item quantity via PUT /items/{id}
    ↓
System checks: Is quantity < user's threshold?
    ↓ YES
Create/Update LowStockAlert record
    ↓
Send Email Notification (if email provided)
    ↓
Send WhatsApp Notification (if phone provided)
    ↓
Set next_alert_at to 24 hours later (spam prevention)
```

**Example:**
```bash
PUT /items/5
{
  "name": "Resistor 1K",
  "quantity": 3,        # Was 50, now 3 < threshold 5
  "buying_price": 0.50,
  "selling_price": 1.00,
  "description": "...",
  "model_number": "RES-1K",
  "category_id": 1
}
```

### 2. Daily Automated Check (9:00 AM UTC)

**Flow:**
```
Daily scheduler triggers at 9:00 AM UTC
    ↓
For each unresolved alert:
  - Check if item still has low stock
  - Check if 24 hours have passed since last alert
  ↓ YES to both
  - Update last_sent_at and next_alert_at
  - Send reminder notification
  ↓ Item now has stock
  - Mark alert as resolved
```

---

## 📧 Email Notifications

### Email Template
The system sends beautifully formatted HTML emails with:
- ⚠️ Alert icon and title
- Item name and current quantity
- Alert threshold
- Timestamp

**Example Email:**
```
Subject: ⚠️ Low Stock Alert: Resistor 1K

Hi user@example.com,

The following item has low stock:

┌─────────────────────────────────┐
│ Item Name: Resistor 1K          │
│ Current Quantity: 3             │
│ Alert Threshold: 5              │
└─────────────────────────────────┘

Please restock this item to avoid stockouts.

Sent at: 2024-02-02 10:30:45
```

---

## 💬 WhatsApp/SMS Notifications

### WhatsApp Message Template
```
Pujana Inventory Alert 🚨

Item: Resistor 1K
Current Stock: 3
Alert Level: 5

⚠️ Stock is low! Please restock soon.

Reply HELP for more info.
```

---

## 🛡️ Safety Features

### 1. Spam Prevention
- Won't send same alert twice within 24 hours
- Uses `next_alert_at` field to track

### 2. Notification Preferences
- Users can enable/disable notifications
- Set custom alert thresholds per user
- Choose which channels (email, WhatsApp, or both)

### 3. Audit Trail
- All alerts are logged with timestamps
- `created_at` - when alert was first created
- `last_sent_at` - last notification sent time
- `is_resolved` - whether item has been restocked

---

## 🐛 Troubleshooting

### Email Not Sending
**Problem:** "Email credentials not configured"

**Solution:**
1. Check `.env` file has `EMAIL_SENDER` and `EMAIL_PASSWORD`
2. For Gmail: Use App Password (not regular password)
3. Enable "Less secure app access" if not using App Password

---

### WhatsApp Not Sending
**Problem:** "Twilio credentials not configured"

**Solution:**
1. Twilio is optional - system logs warning but continues
2. To enable: Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_NUMBER`
3. Add user's phone number in preferences (format: +919876543210)

---

### Scheduler Not Running
**Problem:** Alerts not sent at 9:00 AM

**Solution:**
1. Check server logs for APScheduler startup message
2. Scheduler runs in UTC timezone
3. Change time in `app/services/scheduler.py` line with `CronTrigger(hour=9, minute=0)`

---

### Alert Not Created When Quantity Changes
**Problem:** Item updated but alert not created

**Debugging:**
1. Check `notification_enabled` is `true` for user
2. Check `alert_threshold` value
3. Check quantity is actually below threshold
4. Check logs for error messages

---

## 📊 Database Schema

### Users Table (Updated)
```sql
ALTER TABLE users ADD COLUMN phone_number VARCHAR;
ALTER TABLE users ADD COLUMN notification_email VARCHAR;
ALTER TABLE users ADD COLUMN notification_enabled BOOLEAN DEFAULT true;
ALTER TABLE users ADD COLUMN alert_threshold INTEGER DEFAULT 5;
```

### LowStockAlerts Table (New)
```sql
CREATE TABLE low_stock_alerts (
    id SERIAL PRIMARY KEY,
    item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quantity_at_alert INTEGER NOT NULL,
    alert_type VARCHAR NOT NULL,  -- 'EMAIL', 'WHATSAPP', 'BOTH'
    is_resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT now(),
    last_sent_at TIMESTAMP,
    next_alert_at TIMESTAMP
);
```

---

## 🚀 Advanced Features

### Custom Scheduler Job
Run a one-time check after specific hours:
```python
from app.services.scheduler import add_manual_check_job

# Check in 2 hours
add_manual_check_job(check_time_hours=2)
```

### Get Low Stock Items
```python
from app.services.alert_service import AlertService

alerts = AlertService.get_all_low_stock_items(db, user_id=1)
```

### Programmatically Resolve Alert
```python
from app.services.alert_service import AlertService

AlertService.resolve_alert(db, item_id=5, user_id=1)
```

---

## 📝 Example Usage Flow

### Step 1: User Registration & Setup Preferences
```bash
# Register user (existing API)
POST /users/register
{
  "email": "store@example.com",
  "password": "secure_password"
}

# Update preferences
PUT /alerts/preferences/update
{
  "phone_number": "+919876543210",
  "notification_email": "alerts@example.com",
  "notification_enabled": true,
  "alert_threshold": 5
}
```

### Step 2: Create Item
```bash
POST /items/
{
  "name": "LED Red",
  "quantity": 100,
  "buying_price": 2.00,
  "selling_price": 5.00,
  "model_number": "LED-RED-5MM",
  "category_id": 1
}
```

### Step 3: Update Quantity (Triggers Alert)
```bash
PUT /items/5
{
  "name": "LED Red",
  "quantity": 3,          # Below threshold of 5
  "buying_price": 2.00,
  "selling_price": 5.00,
  "model_number": "LED-RED-5MM",
  "category_id": 1
}

# 📧 Email sent to alerts@example.com
# 💬 WhatsApp sent to +919876543210
```

### Step 4: Check Alerts
```bash
GET /alerts/
# Returns all active alerts

GET /alerts/stats
# Shows alert statistics
```

### Step 5: Restock & Resolve
```bash
PUT /items/5
{
  "quantity": 50    # Back to normal
}

# Alert automatically resolved in next daily check
# OR manually resolve:
PUT /alerts/1/resolve
```

---

## 🎓 Learning Points

As a student, here's what you learned:

1. **Database Design:**
   - Foreign keys and relationships
   - Cascade deletes
   - Timestamps for audit trails

2. **Backend Architecture:**
   - Service layer pattern
   - Router/controller pattern
   - Dependency injection (FastAPI Depends)

3. **Async Operations:**
   - Background scheduler (APScheduler)
   - Non-blocking notifications
   - Cron jobs

4. **Third-party Integrations:**
   - SMTP for email
   - Twilio API for WhatsApp
   - REST API calls

5. **Best Practices:**
   - Error handling
   - Logging
   - Configuration management (.env)
   - Environment separation

---

## 📞 Support

For issues or questions:
1. Check logs in terminal
2. Review `.env` configuration
3. Verify database migrations ran successfully
4. Check API endpoints with Postman/cURL

---

## ✅ Checklist for Deployment

- [ ] `.env` file configured with all credentials
- [ ] Database migrations run successfully
- [ ] Email credentials verified (test email send)
- [ ] Twilio configured (if using WhatsApp)
- [ ] Scheduler logs show startup message
- [ ] Test alert creation by updating item quantity
- [ ] Verify email received
- [ ] Verify WhatsApp received
- [ ] Test alert preferences update
- [ ] Test alert resolution

---

Great job! You now have a production-ready low stock alert system! 🎉
