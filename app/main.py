from fastapi import FastAPI

app = FastAPI(title="Inventory System")

@app.get("/")
def root():
    return {"message": "Inventory backend running "}
