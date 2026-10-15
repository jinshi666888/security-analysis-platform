from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# 收益状态：pending=待结算 available=可提现 withdrawn=已提现
EARNING_STATUS = ("pending", "available", "withdrawn")


class Earning(Base):
    """收益明细：来源某次 SRC 提交，归属于提交人。"""
    __tablename__ = "earnings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    submission_id: Mapped[int] = mapped_column(Integer, index=True, default=0)
    platform: Mapped[str] = mapped_column(String(64), default="", index=True)
    amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(16), default="CNY")
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    remark: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
