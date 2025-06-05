# app.core.db_mixins.py
from sqlalchemy import Column, DateTime, func
from datetime import datetime, timezone
from app.core.database import Base

class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps to a model."""
    __abstract__ = True # This class is not a table, so it should not be instantiated directly.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
