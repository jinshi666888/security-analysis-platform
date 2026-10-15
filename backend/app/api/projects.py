from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.config import settings
from app.database import get_db
from app.models import Project, User
from app.schemas.project import ProjectCreate, ProjectOut
from app.services import audit

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db),
                        _: User = Depends(get_current_user)):
    result = await db.execute(select(Project).order_by(Project.id.desc()))
    return result.scalars().all()


@router.post("", response_model=ProjectOut)
async def create_project(req: ProjectCreate, db: AsyncSession = Depends(get_db),
                         user: User = Depends(require_role("admin"))):
    src = Path(req.source_path)
    if not src.is_dir():
        raise HTTPException(400, f"源码路径不存在: {req.source_path}")
    if not req.name.strip():
        raise HTTPException(400, "项目名不能为空")
    dup = await db.execute(select(Project).where(Project.name == req.name))
    if dup.scalar_one_or_none():
        raise HTTPException(400, f"项目名已存在: {req.name}")
    out_dir = str(Path(settings.default_out_root) / req.name) if settings.default_out_root else ""
    project = Project(name=req.name, source_path=str(src.resolve()),
                      out_dir=out_dir, scanners=req.scanners)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    await audit.record(db, user, "project.create", project.name,
                       f"source={project.source_path} scanners={project.scanners}")
    return project


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db),
                      _: User = Depends(get_current_user)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    return project


@router.delete("/{project_id}")
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db),
                         user: User = Depends(require_role("admin"))):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    name = project.name
    await db.delete(project)
    await db.commit()
    await audit.record(db, user, "project.delete", name, "")
    return {"ok": True}
