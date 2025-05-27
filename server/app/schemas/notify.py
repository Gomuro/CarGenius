# app/schema/notify.py
from pydantic import BaseModel
from typing import Literal

class NotificationIn(BaseModel):
    """Notification input schema for incoming WebSocket messages."""
    type: Literal["message", "ping", "alert"]
    content: str


class NotificationOut(BaseModel):
    """Notification output schema for outgoing WebSocket messages."""
    type: Literal["broadcast", "personal", "system"]
    content: str
