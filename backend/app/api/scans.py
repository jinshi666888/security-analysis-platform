from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.config import settings
from app.database import get_db
from app.models import Project, ScanRun, User
from app.services import audit
from app.services.scanner import run_scan

router = APIRouter(prefix="/scans", tags=["scans"])


@router.post("/{project_id}")
async def trigger_scan(project_id: int, db: AsyncSession = Depends(get_db),
                       user: User = Depends(require_role("admin", "analyst"))):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    if not Path(project.source_path).is_dir():
        raise HTTPException(400, f"源码路径不存在: {project.source_path}")
    out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    run = ScanRun(project_id=project_id, status="running", out_dir=out_dir,
                  started_at=datetime.utcnow())
    db.add(run)
    await db.commit()
    await db.refresh(run)

    result = await run_scan(project.name, project.source_path, out_dir, project.scanners)
    run.status = "done" if result["returncode"] in (0, 10, 20) else "failed"
    run.finished_at = datetime.utcnow()
    run.summary = result["stdout"][-1000:]
    project.last_scan_at = datetime.utcnow()
    try:
        gate = json.loads(Path(out_dir, "security-gate.json").read_text(encoding="utf-8"))
        project.last_gate_status = "passed" if gate.get("passed") else "blocked"
    except Exception:
        project.last_gate_status = "unknown"
    await db.commit()
    await audit.record(db, user, "scan.trigger", project.name,
                       f"run_id={run.id} status={run.status} rc={result['returncode']}")
    return {"run_id": run.id, "status": run.status, "out_dir": out_dir,
            "returncode": result["returncode"]}


@router.get("/{project_id}/history")
async def scan_history(project_id: int, db: AsyncSession = Depends(get_db),
                       _: User = Depends(get_current_user)):
    result = await db.execute(select(ScanRun).where(ScanRun.project_id == project_id)
                              .order_by(ScanRun.id.desc()).limit(20))
    runs = result.scalars().all()
    return [{"id": r.id, "status": r.status, "out_dir": r.out_dir,
             "started_at": r.started_at, "finished_at": r.finished_at,
             "summary": r.summary} for r in runs]
