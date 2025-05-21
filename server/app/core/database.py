# server/app/core/database.py
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base


SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url
# Create an asynchronous SQLAlchemy engine
# echo=True enables SQL logging for debugging; set to False in production
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)

# Create an asynchronous session factory
# expire_on_commit=False prevents SQLAlchemy from expiring objects after commit
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all ORM models
Base = declarative_base()
# MetaData object used for table definitions and migrations
metadata = MetaData()

async def get_db():
    """
    Provides a database session for interacting with the database. Used as a dependency in FastAPI routes.
    Yields an AsyncSession object to be used in FastAPI dependencies. Creates a new asynchronous session,
    gives it to the route. Ensures that the session is properly closed after use.
    """    
    async with async_session_maker() as session:
        yield session
