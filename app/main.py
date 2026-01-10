from fastapi import FastAPI
from app.models import user as models
from app.database import engine, test_db_connection
from app.routers import user , category

app = FastAPI(title="Inventory System")

models.Base.metadata.create_all(bind=engine)

app.include_router(user.router)
app.include_router(category.router)

@app.on_event("startup")
def startup_event():
    test_db_connection()
    models.Base.metadata.create_all(bind=engine)
    
    
@app.get("/")
def root():
    return {"message": "Inventory backend running "}