# Backend Code Changes - Quick Reference

## File 1: app/utils.py - COMPLETE REPLACEMENT

```python
from passlib.context import CryptContext

# Use bcrypt with proper configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

# Function to hash password
def hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password
        
    Raises:
        ValueError: If password is longer than 72 bytes
    """
    password = str(password).strip()

    # bcrypt limit check - must be 72 bytes or less
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must be 72 bytes or less when encoded as UTF-8")

    try:
        return pwd_context.hash(password)
    except Exception as e:
        raise ValueError(f"Password hashing failed: {str(e)}")

# Function to verify password
def verify(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify
        hashed_password: The hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        return False
```

## File 2: app/main.py - ADD CORS IMPORT & MIDDLEWARE

### Add this import at the top:
```python
from fastapi.middleware.cors import CORSMiddleware
```

### Full file structure:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import user as models
from app.database import engine
from app.routers import user , category , item ,   bill , bill_print , alert
from app.services.scheduler import start_scheduler, stop_scheduler

app = FastAPI(title="Inventory System")

# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods including OPTIONS
    allow_headers=["*"],  # Allow all headers
)

# Start scheduler on app startup
@app.on_event("startup")
def startup_event():
    start_scheduler()

# Stop scheduler on app shutdown
@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

app.include_router(user.router)
app.include_router(category.router)
app.include_router(item.router)
app.include_router(bill.router)
app.include_router(bill_print.router)
app.include_router(alert.router)

    
@app.get("/")
def root():
    return {"message": "Inventory backend running "}
```

## File 3: requirements.txt - UPDATE

### Changes:
1. Change line with `bcrypt==5.0.0` to `bcrypt==4.1.2`
2. Add `reportlab==4.0.9` (after packaging=25.0)
3. Remove duplicate `python-dotenv==1.2.1` (line 67)
4. Remove `python-dotenv==1.2.1` at the end (keep only one)

### Full updated requirements.txt:
```
alembic==1.17.2
annotated-doc==0.0.4
annotated-types==0.7.0
anyio==4.12.1
asyncpg==0.31.0
bcrypt==4.1.2
black==25.12.0
certifi==2026.1.4
click==8.3.1
dnspython==2.8.0
ecdsa==0.19.1
email-validator==2.3.0
fastapi==0.128.0
fastapi-cli==0.0.20
fastapi-cloud-cli==0.9.0
fastar==0.8.0
greenlet==3.3.0
h11==0.16.0
httpcore==1.0.9
httptools==0.7.1
httpx==0.28.1
idna==3.11
isort==7.0.0
itsdangerous==2.2.0
Jinja2==3.1.6
Mako==1.3.10
markdown-it-py==4.0.0
MarkupSafe==3.0.3
mdurl==0.1.2
mypy_extensions==1.1.0
orjson==3.11.5
packaging==25.0
passlib==1.7.4
pathspec==1.0.3
platformdirs==4.5.1
pyasn1==0.6.1
pydantic==2.12.5
pydantic-extra-types==2.11.0
pydantic-settings==2.12.0
pydantic_core==2.41.5
Pygments==2.19.2
python-dotenv==1.2.1
python-jose==3.5.0
python-multipart==0.0.21
pytokens==0.3.0
PyYAML==6.0.3
reportlab==4.0.9
rich==14.2.0
rich-toolkit==0.17.1
rignore==0.7.6
rsa==4.9.1
sentry-sdk==2.49.0
shellingham==1.5.4
six==1.17.0
SQLAlchemy==2.0.45
starlette==0.50.0
typer==0.21.1
typing-inspection==0.4.2
typing_extensions==4.15.0
ujson==5.11.0
urllib3==2.6.3
uvicorn==0.40.0
uvloop==0.22.1
watchfiles==1.1.1
websockets==15.0.1
APScheduler==3.10.4
requests==2.31.0
twilio==9.2.0
```

## Summary of Fixes

| Error | File | Fix |
|-------|------|-----|
| `ValueError: password cannot be longer than 72 bytes` | `app/utils.py` | Updated CryptContext, proper error handling |
| `405 Method Not Allowed for OPTIONS` | `app/main.py` | Added CORSMiddleware |
| `ModuleNotFoundError: No module named 'reportlab'` | `requirements.txt` | Added reportlab==4.0.9 |
| `ImportError: email-validator is not installed` | `requirements.txt` | Ensured email-validator==2.3.0 |
| Duplicate `python-dotenv` | `requirements.txt` | Removed duplicate entry |

## Installation Commands (Manual)

1. Edit `requirements.txt` - make changes shown above
2. Edit `app/utils.py` - replace entire file with code shown above
3. Edit `app/main.py` - add import and middleware shown above
4. Run in terminal:
   ```bash
   cd /Users/chamudikapramod/FastAPI/pujana_electrical/backend
   source venv/bin/activate
   pip install --upgrade -r requirements.txt
   uvicorn app.main:app --reload
   ```

## Verification

After updates, you should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

And frontend at `http://localhost:3000` should be able to:
- Register users ✅
- Login ✅
- Make API calls ✅
- No 405 errors ✅
- No bcrypt errors ✅
