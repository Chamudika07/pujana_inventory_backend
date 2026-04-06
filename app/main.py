from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models import user as models
from app.database import engine
from app.routers import alert, bill, bill_print, category, customer, dashboard, item, payment, supplier, user
from app.services.scheduler import start_scheduler, stop_scheduler
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Inventory System")

# Add CORS middleware to handle cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://localhost:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002", 
        "http://127.0.0.1:3003",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Start scheduler on app startup
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Starting up application...")
    try:
        start_scheduler()
        logger.info("✅ Scheduler initialized successfully")
    except Exception as e:
        logger.error(f"❌ Error starting scheduler: {str(e)}")

# Stop scheduler on app shutdown
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 Shutting down application...")
    stop_scheduler()

app.include_router(user.router)
app.include_router(category.router)
app.include_router(item.router)
app.include_router(bill.router)
app.include_router(bill_print.router)
app.include_router(alert.router)
app.include_router(customer.router)
app.include_router(supplier.router)
app.include_router(payment.router)
app.include_router(dashboard.router)

    
@app.get("/")
def root():
    return {"message": "Inventory backend running"}
