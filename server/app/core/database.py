from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine


SQLALCHEMY_DATABASE_URL = settings.database_url
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)    # echo=False for production

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()
metadata = MetaData()

async def get_db():
    """
    Dependency that provides a database session.
    """
    async with AsyncSessionLocal() as session:
        yield session
