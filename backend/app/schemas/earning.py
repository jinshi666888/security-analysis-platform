from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class EarningCreate(BaseModel):
    submission_id: int = 0
    platform: str = ""
    amount: float = 0.0
    currency: str = "CNY"
    status: str = "pending"
    remark: str = ""


class EarningOut(BaseModel):
    id: int
    user_id: int
    submission_id: int
    platform: str
    amount: float
    currency: str
    status: str
    remark: str
    created_at: datetime

    class Config:
        from_attributes = True
