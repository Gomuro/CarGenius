# app/models/license.py
from sqlalchemy import Column, DateTime, String, Integer, Boolean
from datetime import datetime, timezone
from uuid import uuid4
from app.core.database import Base


class LicenseKey(Base):
    __tablename__ = "license_keys"

    key = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=True)
    client_info = Column(String, nullable=True)
