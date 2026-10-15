from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), index=True)
    source_path: Mapped[str] = mapped_column(String(512))
    out_dir: Mapped[str] = mapped_column(String(512), default="")
    scanners: Mapped[str] = mapped_column(Text, default="builtin-regex,semgrep,trivy,gitleaks,osv")
    config_json: Mapped[str] = mapped_column(Text, default="{}")
    last_scan_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_gate_status: Mapped[str] = mapped_column(String(32), default="unknown")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
