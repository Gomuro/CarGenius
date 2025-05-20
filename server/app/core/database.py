from sqlalchemy.orm import sessionmaker
# from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base


SQLALCHEMY_DATABASE_URL = settings.database_url
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True, future=True)    # echo=False for production

async_session_maker = async_sessionmaker(
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
    async with async_session_maker() as session:
        yield session
