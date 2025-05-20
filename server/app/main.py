# app.main.py
from fastapi import FastAPI
from app.routers import license

app = FastAPI()
app.include_router(license.router, prefix="/license", tags=["license"])


@app.get("/")
async def health_check():
    return {"status": "ok"}