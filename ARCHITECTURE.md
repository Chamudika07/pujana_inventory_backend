# Architecture Diagram - Low Stock Alert System

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION                        │
│                      (app/main.py)                                  │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   ROUTERS        │    │   SERVICES       │    │   MODELS         │
│                  │    │                  │    │                  │
├──────────────────┤    ├──────────────────┤    ├──────────────────┤
│ • item.py        │    │ • notification   │    │ • item.py        │
│   (triggers)     │    │   _service.py    │    │   (updated)      │
│                  │    │                  │    │                  │
│ • alert.py       │    │ • alert_service  │    │ • user.py        │
│   (8 endpoints)  │    │   .py            │    │   (updated)      │
│                  │    │                  │    │                  │
│ • user.py        │    │ • scheduler.py   │    │ • low_stock_     │
│ • category.py    │    │   (daily jobs)   │    │   alert.py       │
│ • bill.py        │    │                  │    │   (NEW)          │
└──────────────────┘    └──────────────────┘    └──────────────────┘
                                │
                   ┌────────────┼────────────┐
                   │            │            │
                   ▼            ▼            ▼
        ┌──────────────┐  ┌──────────┐  ┌────────────┐
        │   DATABASE   │  │  SMTP    │  │  TWILIO    │
        │ PostgreSQL   │  │  Server  │  │ (WhatsApp) │
        │              │  │ (Gmail)  │  │            │
        │ • users      │  │          │  │ API        │
        │ • items      │  │ Outgoing │  │            │
        │ • alerts     │  │ Email    │  │ Outgoing   │
        │ • category   │  │          │  │ WhatsApp   │
        │ • bills      │  │          │  │            │
        └──────────────┘  └──────────┘  └────────────┘
                   │            │            │
                   └────────────┼────────────┘
                                │
                   ┌────────────┴────────────┐
                   │                         │
                   ▼                         ▼
              ┌──────────────┐        ┌──────────────┐
              │    USER      │        │    USER      │
              │   EMAIL      │        │  WHATSAPP    │
              └──────────────┘        └──────────────┘
```

---

## Data Flow - Real-Time Alert

```
                    USER API REQUEST
                           │
                           ▼
                  PUT /items/{id}
                  Update quantity: 100 → 3
                           │
                           ▼
        ┌─────────────────────────────────┐
        │ ItemRouter.update_item()         │
        │ • Update database                │
        │ • Commit changes                 │
        └──────────────┬────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────┐
        │ Check Alert Trigger             │
        │ quantity_changed?                │
        └──────────────┬────────────────────┘
                       │
                   YES │ NO
                   ┌───┘        └─── No Action
                   │
                   ▼
        ┌─────────────────────────────────┐
        │ AlertService.check_and_create_  │
        │ alert()                          │
        │                                  │
        │ Is quantity < threshold?         │
        └──────────────┬────────────────────┘
                       │
                   YES │ NO
                   ┌───┘        └─── Return False
                   │
                   ▼
        ┌─────────────────────────────────┐
        │ Create/Update LowStockAlert      │
        │ • Check 24-hour spam rule       │
        │ • Set timestamps                │
        │ • Save to database              │
        └──────────────┬────────────────────┘
                       │
                       ▼
        ┌─────────────────────────────────┐
        │ Send Notifications              │
        │ (async operations)              │
        └──────────────┬────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
   ┌─────────────┐            ┌──────────────┐
   │ Send Email  │            │Send WhatsApp │
   │             │            │              │
   │ • SMTP      │            │ • Twilio API │
   │ • Gmail     │            │ • Phone      │
   │ • To: user  │            │ • To: user   │
   └─────────────┘            └──────────────┘
        │                             │
        ▼                             ▼
   ┌─────────────┐            ┌──────────────┐
   │   EMAIL ✓   │            │ WHATSAPP ✓   │
   │  RECEIVED   │            │  RECEIVED    │
   └─────────────┘            └──────────────┘
```

---

## Data Flow - Daily Scheduler

```
           START APPLICATION
                   │
                   ▼
        ┌──────────────────────────┐
        │ Scheduler.start_scheduler()
        │                          │
        │ Add CronTrigger:         │
        │ • Time: 09:00 UTC        │
        │ • Job: daily_check()     │
        │ • Recurrence: Daily      │
        └──────────────┬───────────┘
                       │
                       │ (Wait until 9:00 AM UTC)
                       │
    ╔══════════════════════════════════════╗
    ║      EVERY DAY AT 9:00 AM UTC        ║
    ╚════════════════════╤═════════════════╝
                        │
                        ▼
        ┌──────────────────────────┐
        │ daily_low_stock_check()  │
        │                          │
        │ Get all unresolved       │
        │ alerts from database     │
        └──────────────┬───────────┘
                       │
                       ▼
        ┌──────────────────────────────────┐
        │ For each alert:                  │
        │                                  │
        │ 1. Get item & check quantity     │
        │ 2. Check if 24h passed           │
        │ 3. Check if enabled              │
        └──────────────┬───────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        │                             │
   Stock LOW?              Stock HIGH?
        │                             │
        ▼                             ▼
   ┌──────────────┐         ┌─────────────────┐
   │ Send          │         │ Resolve Alert   │
   │ REMINDER      │         │                 │
   │ Notification  │         │ Mark as         │
   │               │         │ resolved=true   │
   │ Update:       │         │                 │
   │ • last_sent   │         │ Done ✓          │
   │ • next_alert  │         └─────────────────┘
   └──────────────┘
```

---

## Database Schema

```
┌─────────────────────────────────────────────────────┐
│                        USERS                         │
├──────────────────────────────────────────────────────┤
│ id (PK)                                              │
│ email                                                │
│ password                                             │
│ phone_number ★ (NEW)                                 │
│ notification_email ★ (NEW)                           │
│ notification_enabled ★ (NEW, default: true)          │
│ alert_threshold ★ (NEW, default: 5)                  │
│ created_at                                           │
└──────────────────────────────────────────────────────┘
         │                                        ▲
         │                                        │
         │ (1:M)                          (1:M)   │
         │                                        │
         ▼                                        │
┌─────────────────────────────────────┐          │
│      LOW_STOCK_ALERTS (NEW)         │          │
├─────────────────────────────────────┤          │
│ id (PK)                             │          │
│ item_id (FK) ─────────┐             │          │
│ user_id (FK) ─────────┼─────────────┘          │
│ quantity_at_alert     │                        │
│ alert_type            │ BOTH, EMAIL, WHATSAPP  │
│ is_resolved           │                        │
│ created_at            │                        │
│ last_sent_at          │ (24h prevention)       │
│ next_alert_at         │                        │
└─────────────────────────────────────┘          │
         │                                        │
         │ (M:1)                                 │
         │                                        │
         ▼                                        │
┌─────────────────────────────────────┐          │
│           ITEMS                     │          │
├─────────────────────────────────────┤          │
│ id (PK)                             │          │
│ name                                │          │
│ quantity                            │          │
│ buying_price                        │          │
│ selling_price                       │          │
│ description                         │          │
│ model_number                        │          │
│ category_id (FK)                    │          │
│ low_stock_alerts (relationship) ◄───┘          │
│ inventory_transaction (relationship)           │
│ created_at                                     │
└─────────────────────────────────────┘
```

---

## Service Layer Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    API LAYER (Routers)                  │
│                                                          │
│  • item.py (PUT /{id})  ◄─── Triggers alert check       │
│  • alert.py (8 endpoints) ◄─── Alert management         │
│  • user.py                                              │
│  • category.py                                          │
│  • bill.py                                              │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│                  SERVICE LAYER                          │
│                                                          │
│  ┌─────────────────────────────────────┐               │
│  │ AlertService                        │               │
│  │ • check_and_create_alert()          │               │
│  │ • send_alert_notifications()        │               │
│  │ • resolve_alert()                   │               │
│  │ • get_all_low_stock_items()         │               │
│  └────────────────┬────────────────────┘               │
│                   │                                     │
│  ┌────────────────▼────────────────────┐               │
│  │ NotificationService                 │               │
│  │ • send_email()                      │               │
│  │ • send_whatsapp()                   │               │
│  │ • create_*_template()               │               │
│  └────────────────┬────────────────────┘               │
│                   │                                     │
│  ┌────────────────▼────────────────────┐               │
│  │ Scheduler Service                   │               │
│  │ • start_scheduler()                 │               │
│  │ • stop_scheduler()                  │               │
│  │ • daily_low_stock_check()           │               │
│  └─────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────┘
```

---

## API Endpoint Structure

```
/alerts
├── GET / ........................... Get all alerts
├── GET /stats ...................... Get statistics
├── GET /{alert_id} ................ Get specific alert
├── PUT /{alert_id}/resolve ........ Mark as resolved
├── preferences
│   ├── GET /get ................... Get user preferences
│   └── PUT /update ............... Update preferences
└── POST /trigger-check ............ Manual check trigger
```

---

## Notification Channels

```
                    ALERT SYSTEM
                          │
                ┌─────────┴─────────┐
                │                   │
        Channel 1         Channel 2  Channel 3
         (Email)         (WhatsApp)  (Future)
                │                   │
                ▼                   ▼
        ┌──────────────┐     ┌────────────────┐
        │ SMTP Server  │     │  Twilio API    │
        │   (Gmail)    │     │  (WhatsApp)    │
        │              │     │                │
        │ Credentials: │     │ Credentials:   │
        │ • Sender     │     │ • Account SID  │
        │ • Password   │     │ • Auth Token   │
        │ • Server     │     │ • Phone Number │
        └──────┬───────┘     └────────┬───────┘
               │                      │
               ▼                      ▼
        ┌──────────────┐     ┌────────────────┐
        │ USER EMAIL   │     │ USER WHATSAPP  │
        │              │     │                │
        │ Received ✓   │     │ Received ✓     │
        └──────────────┘     └────────────────┘
```

---

## Configuration & Environment

```
.env File
├── Database Config
│   ├── DATABASE_HOSTNAME
│   ├── DATABASE_PORT
│   ├── DATABASE_USERNAME
│   ├── DATABASE_PASSWORD
│   └── DATABASE_NAME
│
├── Email Config
│   ├── SMTP_SERVER
│   ├── SMTP_PORT
│   ├── EMAIL_SENDER
│   └── EMAIL_PASSWORD
│
├── Twilio Config (Optional)
│   ├── TWILIO_ACCOUNT_SID
│   ├── TWILIO_AUTH_TOKEN
│   └── TWILIO_WHATSAPP_NUMBER
│
└── App Config
    ├── SECRET_KEY
    ├── ALGORITHM
    └── ACCESS_TOKEN_EXPIRE_MINUTES
```

---

## Deployment Checklist

```
┌─────────────────────────────────────┐
│ BEFORE DEPLOYMENT                   │
├─────────────────────────────────────┤
│ ✓ .env configured                   │
│ ✓ Database created                  │
│ ✓ Migrations run                    │
│ ✓ Email tested                      │
│ ✓ WhatsApp tested                   │
│ ✓ Scheduler verified                │
│ ✓ Tests passing                     │
│ ✓ Error handling in place           │
│ ✓ Logging configured                │
│ ✓ Security review done              │
└─────────────────────────────────────┘
         │
         ▼
    READY FOR
    PRODUCTION
```

---

This architecture ensures:
- ✅ **Scalability** - Service layer can be replicated
- ✅ **Maintainability** - Clean separation of concerns
- ✅ **Testability** - Each layer can be tested independently
- ✅ **Reliability** - Error handling at each layer
- ✅ **Performance** - Async operations for notifications
