# server/app/models/cargurus.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON
from app.core.database import Base

class CarGurus(Base):
    __tablename__ = "cargurus"
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(String, unique=True, index=True, nullable=False)
    label = Column(String, index=True)
    """Add vim in future"""

