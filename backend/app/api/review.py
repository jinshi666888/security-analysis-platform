"""人工复核：调用 runtime 的 review 命令。"""
from __future__ import annotations

import asyncio
import json
import subprocess
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.config import settings
from app.database import get_db
from app.models import Project, User
from app.schemas.review import ReviewBatch
from app.services import audit

router = APIRouter(prefix="/review", tags=["review"])


@router.get("/{project_id}/pending")
async def pending_review(project_id: int, db: AsyncSession = Depends(get_db),
                         _: User = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    fp = Path(out_dir) / "findings.json"
    if not fp.is_file():
        return []
    doc = json.loads(fp.read_text(encoding="utf-8"))
    pending = [{"id": f["id"], "severity": f["severity"], "type": f["type"],
                "file": f["file"], "line": f["line"], "status": f.get("status", "")}
               for f in doc.get("findings", [])
               if f.get("status") in ("triaged", "needs_review", "")]
    return pending


@router.post("/{project_id}")
async def apply_review(project_id: int, batch: ReviewBatch,
                       db: AsyncSession = Depends(get_db),
                       user: User = Depends(require_role("admin", "analyst"))):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    if not batch.items:
        raise HTTPException(400, "复核结论为空")
    runtime = Path(settings.runtime_path)
    main_py = runtime / "main.py"
    if not main_py.is_file():
        raise HTTPException(500, f"runtime 不存在: {settings.runtime_path}")
    out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    decisions = {"decisions": {item.finding_id: item.decision for item in batch.items}}
    dec_file = Path(out_dir) / "_review_decisions.json"
    dec_file.parent.mkdir(parents=True, exist_ok=True)
    dec_file.write_text(json.dumps(decisions, ensure_ascii=False), encoding="utf-8")
    cmd = [settings.python_exe, str(main_py), "review", project.source_path,
           "--out", out_dir, "--from-file", str(dec_file),
           "--reviewer", batch.reviewer or "platform", "--note", batch.note]
    # 子进程为阻塞调用，放入线程池避免卡住事件循环
    proc = await asyncio.to_thread(
        subprocess.run, cmd, capture_output=True, text=True, cwd=str(runtime))
    await audit.record(db, user, "review.apply", project.name,
                       f"count={len(batch.items)} rc={proc.returncode} "
                       f"decision={batch.items[0].decision if batch.items else ''}")
    return {"returncode": proc.returncode, "stdout": proc.stdout[-2000:],
            "stderr": proc.stderr[-1000:]}
