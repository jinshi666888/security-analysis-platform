from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class SrcSubmissionCreate(BaseModel):
    task_id: int | None = None
    project_id: int | None = None
    finding_id: str = ""
    title: str
    platform: str = ""
    severity: str = "medium"
    status: str = "draft"
    reward_amount: float = 0.0
    asset: str = ""
    vuln_type: str = ""
    note: str = ""


class SrcSubmissionFromFinding(BaseModel):
    """从本地 confirmed 漏洞一键登记为 SRC 提交。"""
    project_id: int
    finding_id: str
    platform: str = ""
    task_id: int | None = None
    note: str = ""


class SrcSubmissionUpdate(BaseModel):
    status: str | None = None
    reward_amount: float | None = None
    note: str = ""


class SrcSubmissionOut(BaseModel):
    id: int
    task_id: int | None
    project_id: int | None
    finding_id: str
    title: str
    platform: str
    severity: str
    status: str
    reward_amount: float
    asset: str
    vuln_type: str
    note: str
    timeline: list[dict]
    submitted_at: datetime | None
    resolved_at: datetime | None
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
