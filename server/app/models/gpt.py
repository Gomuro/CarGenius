# app/models/gpt.py
from sqlalchemy import Column, String, Text, Integer, DateTime, func
from app.core.database import Base


class GPTPromptLog(Base):
    __tablename__ = "gpt_prompt_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    gpt_prompt = Column(Text)
    gpt_response = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())
