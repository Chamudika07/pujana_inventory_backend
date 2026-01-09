from fastapi import FastAPI
from app.models import user as models
from app.database import engine, test_db_connection


app = FastAPI(title="Inventory System")

models.Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def startup_event():
    test_db_connection()
    models.Base.metadata.create_all(bind=engine)
    
    
@app.get("/")
def root():
    return {"message": "Inventory backend running "}