# app/tests/conftest.py
import asyncio

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core import database
from app.core.config import TEST_DATABASE_URL
from app.core.database import async_session_maker

test_engine = create_async_engine(TEST_DATABASE_URL, future=True)  # Create an asynchronous engine for the test database
TestSessionLocal = async_sessionmaker(test_engine,
                                      expire_on_commit=False)  # Create a session factory for the test database
database.async_session_maker = TestSessionLocal  # So that the entire app uses the test session instead of the production one.

from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture  # Marks this function as a pytest fixture (used to provide reusable test setup)
async def client():
    # # Create an async HTTP client using HTTPX with ASGI transport to test the FastAPI app without running a server
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac  # Yield the client to be used in the test, then automatically close it when done


@pytest.fixture
async def session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


@pytest.fixture(autouse=True)
async def prepare_db(session: AsyncSession):
    try:
        # Clean up the database before each test
        await session.execute(text("DELETE FROM license_keys"))
        await session.commit()
    except Exception as e:
        pytest.fail(f"Failed to clean database: {str(e)}")
