from fastapi import FastAPI
from app.models import user as models
from app.database import engine
from app.routers import user , category , item , inventory

app = FastAPI(title="Inventory System")



app.include_router(user.router)
app.include_router(category.router)
app.include_router(item.router)

    
@app.get("/")
def root():
    return {"message": "Inventory backend running "}