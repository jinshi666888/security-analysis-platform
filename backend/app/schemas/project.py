from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    source_path: str
    scanners: str = "builtin-regex,semgrep,trivy,gitleaks,osv"


class ProjectOut(BaseModel):
    id: int
    name: str
    source_path: str
    out_dir: str
    scanners: str
    last_scan_at: datetime | None
    last_gate_status: str
    created_at: datetime

    class Config:
        from_attributes = True
