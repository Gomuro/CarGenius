from fastapi import FastAPI
from app.routers import license

app = FastAPI()
app.include_router(license.router, prefix="/license", tags=["license"])
