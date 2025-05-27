# app/main.py
from fastapi import FastAPI, Request
from app.core.rate_limiter import limiter
from app.routers import license, gpt
from fastapi import Request
from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from fastapi.middleware.cors import \
    CORSMiddleware  # security feature that allows or restricts web applications from making requests to a server on a different origin (domain).

app = FastAPI()
API_PREFIX = "/api/v1"

app.state.limiter = limiter  # Attach the rate limiter instance to the FastAPI app state for global access

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request,
                             exc: RateLimitExceeded):  # Register a global exception handler to catch and handle rate limit exceeded errors
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "message": str(exc)
        }
    )

# Middleware to handle CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(license.router, prefix=f"{API_PREFIX}/license", tags=["license"])
app.include_router(gpt.router, prefix=f"{API_PREFIX}/gpt", tags=["gpt"])
