from __future__ import annotations

from pydantic import BaseModel


class ReviewItem(BaseModel):
    finding_id: str
    decision: str


class ReviewBatch(BaseModel):
    items: list[ReviewItem]
    reviewer: str = ""
    note: str = ""
