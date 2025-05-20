# server/tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import async_session_maker, get_db

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest_asyncio.fixture
async def override_db():
    async with async_session_maker() as session:
        yield session

@pytest_asyncio.fixture
async def client(override_db: AsyncSession):
    # Замінюємо залежність get_db у FastAPI
    async def _get_test_db():
        yield override_db

    app.dependency_overrides[get_db] = _get_test_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()