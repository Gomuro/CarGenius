# app/exceptions.py
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Global exception handler for rate limit errors.
    """
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "message": str(exc)
        }
    )


async def custom_request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom exception handler for request validation errors.
    Returns a JSON response with the error details.
    """
    errors = exc.errors()
    detail_message = []
    for error in errors:
        loc = error.get("loc", [])
        msg = error.get("msg", "")
        field = loc[-1] if loc else None
        if field:
            detail_message.append(f"Field '{field}: {msg}")
        else:
            detail_message.append(msg)
    return JSONResponse(status_code=HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": detail_message})
