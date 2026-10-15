from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.database import get_db
from app.models import Project, User
from app.services import findings_reader

router = APIRouter(prefix="/findings", tags=["findings"])


@router.get("/{project_id}")
async def list_findings(project_id: int,
                        severity: str | None = None,
                        status: str | None = None,
                        source: str | None = None,
                        cwe: str | None = None,
                        keyword: str | None = None,
                        page: int = Query(1, ge=1),
                        page_size: int = Query(50, ge=1, le=500),
                        db: AsyncSession = Depends(get_db),
                        _: User = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    return findings_reader.list_findings(out_dir, severity=severity, status=status,
                                         source=source, cwe=cwe, keyword=keyword,
                                         page=page, page_size=page_size)


@router.get("/{project_id}/{finding_id}")
async def get_finding(project_id: int, finding_id: str,
                      db: AsyncSession = Depends(get_db),
                      _: User = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    finding = findings_reader.get_finding(out_dir, finding_id)
    if not finding:
        raise HTTPException(404, "漏洞不存在")
    taint = findings_reader.get_taint(out_dir, finding_id)
    return {"finding": finding, "taint": taint}


@router.get("/{project_id}/dashboard/stats")
async def dashboard_stats(project_id: int, db: AsyncSession = Depends(get_db),
                          _: User = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    return findings_reader.dashboard_stats(out_dir)


@router.get("/{project_id}/report/content")
async def get_report(project_id: int, db: AsyncSession = Depends(get_db),
                     _: User = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    return findings_reader.get_report(out_dir)


@router.get("/{project_id}/feedback/rules")
async def get_feedback_rules(project_id: int, db: AsyncSession = Depends(get_db),
                             _: User = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    return findings_reader.get_feedback_rules(out_dir)


@router.get("/{project_id}/benchmark/report")
async def get_benchmark(project_id: int, db: AsyncSession = Depends(get_db),
                        _: User = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    return findings_reader.get_benchmark(out_dir)
