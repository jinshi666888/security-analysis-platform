from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class WithdrawalCreate(BaseModel):
    amount: float
    method: str = "alipay"  # alipay/wechat/bank
    account: str = ""


class WithdrawalReview(BaseModel):
    decision: str  # approve / reject
    note: str = ""


class WithdrawalOut(BaseModel):
    id: int
    user_id: int
    amount: float
    currency: str
    method: str
    account: str
    status: str
    reviewer_id: int | None
    review_note: str
    reviewed_at: datetime | None
    paid_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
