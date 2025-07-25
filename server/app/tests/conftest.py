# app/tests/conftest.py
import asyncio
import os
import shutil
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import TEST_DATABASE_URL

test_engine = create_async_engine(TEST_DATABASE_URL, future=True)  # Create an asynchronous engine for the test database
TestSessionLocal = async_sessionmaker(test_engine,
                                      expire_on_commit=False)  # Create a session factory for the test database
import app.core.database

app.core.database.async_session_maker = TestSessionLocal  # So that the entire app uses the test session instead of the production one.
from app.main import app

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # /home/.../CarGenius/server/app/tests
PROJECT_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))  # /home/.../CarGenius/server

TEST_SOURCE_PATH = os.path.join(CURRENT_DIR, "test_data", "test_car_data_Audi_1.json")
DESTINATION_PATH = os.path.join(PROJECT_ROOT, "car_data_Audi.json")  # path inside a Docker container


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture  # Marks this function as a pytest fixture (used to provide reusable test setup)
async def client():
    # # Create an async HTTP client using HTTPX with ASGI transport to test the FastAPI app without running a server
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac  # Yield the client to be used in the test, then automatically close it when done


@pytest.fixture
async def session() -> AsyncSession:
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
async def prepare_db(session: AsyncSession):
    try:
        # Clean up the database before each test
        await session.execute(text("DELETE FROM license_keys"))
        await session.commit()
    except Exception as e:
        pytest.fail(f"Failed to clean database: {str(e)}")


@pytest.fixture(scope="function", autouse=True)
def copy_test_json_file():
    """Fixture to copy the test JSON file to the current working directory before each test."""
    # Current working directory inside the Docker container (in our case: /workdir_docker)
    cwd = os.getcwd()
    # Path to the test source (always relative to this file)
    test_source = os.path.join(os.path.dirname(__file__), "test_data", "test_car_data_Audi_1.json")
    # Target path (in the same folder where the endpoint is waiting)
    dest = os.path.join(cwd, "car_data_Audi_1.json")

    shutil.copy(test_source, dest)
    yield
    if os.path.exists(dest):
        os.remove(dest)
