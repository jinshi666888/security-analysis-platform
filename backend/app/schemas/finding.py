from __future__ import annotations

from pydantic import BaseModel


class FindingOut(BaseModel):
    id: str
    severity: str
    type: str
    file: str
    line: int | None
    status: str
    source: str
    source_stage: str
    confidence: float | None
    evidence: str
    cwe: str | None
    owasp_id: str | None
    cvss_score: float | None
    priority_level: str | None
    sla: str | None


class FindingListResponse(BaseModel):
    items: list[FindingOut]
    total: int
    page: int
    page_size: int
