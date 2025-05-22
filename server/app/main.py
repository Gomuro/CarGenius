# app/main.py
from fastapi import FastAPI
from app.routers import license, gpt

app = FastAPI()
API_PREFIX = "/api/v1"

app.include_router(license.router, prefix=f"{API_PREFIX}/license", tags=["license"])
app.include_router(gpt.router, prefix=f"{API_PREFIX}/gpt", tags=["gpt"])
