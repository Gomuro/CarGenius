# app/core/rate_limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(
    key_func=get_remote_address)  # Create a rate limiter that limits requests based on the client's IP address
