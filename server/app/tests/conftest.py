import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.database import Base
from app.core import database
from app.core.config import TEST_DATABASE_URL

test_engine = create_async_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
database.async_session_maker = TestSessionLocal # So that the entire app uses the test session instead of the production one.

from app.main import app
from app.core.database import get_db



@pytest.fixture   # Marks this function as a pytest fixture (used to provide reusable test setup)
async def client():
    # Create an async HTTP client using HTTPX with ASGI transport to test the FastAPI app without running a server
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac   # Yield the client to be used in the test, then automatically close it when done
        