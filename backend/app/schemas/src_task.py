from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SrcTaskCreate(BaseModel):
    platform: str
    title: str
    status: str = "open"
    reward_min: float = 0.0
    reward_max: float = 0.0
    currency: str = "CNY"
    scope: str = ""
    url: str = ""
    description: str = ""
    deadline: datetime | None = None


class SrcTaskImport(BaseModel):
    """批量导入：format=csv|json，content 为文本内容。"""
    format: str = "csv"
    content: str


class SrcTaskOut(BaseModel):
    id: int
    platform: str
    title: str
    status: str
    reward_min: float
    reward_max: float
    currency: str
    scope: str
    url: str
    description: str
    deadline: datetime | None
    source: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
