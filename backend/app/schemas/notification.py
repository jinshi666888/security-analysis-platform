from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NotificationOut(BaseModel):
    id: int
    user_id: int
    category: str
    title: str
    content: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
