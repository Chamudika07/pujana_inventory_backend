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