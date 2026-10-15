from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# 提交状态：draft=草稿 submitted=已提交 reviewing=审核中 accepted=已通过
#           rejected=已驳回 duplicate=重复 paid=已发放赏金
SRC_SUBMISSION_STATUS = ("draft", "submitted", "reviewing", "accepted",
                         "rejected", "duplicate", "paid")


class SrcSubmission(Base):
    """SRC 漏洞提交记录，可关联本地 finding（confirmed 漏洞一键登记）。"""
    __tablename__ = "src_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    project_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    finding_id: Mapped[str] = mapped_column(String(128), default="", index=True)
    title: Mapped[str] = mapped_column(String(256))
    platform: Mapped[str] = mapped_column(String(64), default="", index=True)
    severity: Mapped[str] = mapped_column(String(32), default="medium")
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True)
    reward_amount: Mapped[float] = mapped_column(Float, default=0.0)
    asset: Mapped[str] = mapped_column(String(512), default="")
    vuln_type: Mapped[str] = mapped_column(String(128), default="")
    note: Mapped[str] = mapped_column(Text, default="")
    timeline: Mapped[str] = mapped_column(Text, default="[]")  # JSON: [{time,status,note}]
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, index=True, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow,
                                                 onupdate=datetime.utcnow)
