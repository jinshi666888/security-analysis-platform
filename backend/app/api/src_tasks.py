"""SRC 众测任务聚合：手工登记 + CSV/JSON 批量导入 + 筛选分页。"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models import SrcTask, User
from app.schemas.src_task import SrcTaskCreate, SrcTaskImport, SrcTaskOut
from app.services import audit

router = APIRouter(prefix="/src/tasks", tags=["src-tasks"])


def _parse_deadline(value: object) -> datetime | None:
    if not value:
        return None
    text = str(value).strip().replace("/", "-")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _parse_float(value: object) -> float:
    try:
        return float(str(value).replace(",", "").replace("¥", "").strip() or 0)
    except (TypeError, ValueError):
        return 0.0


@router.get("")
async def list_tasks(platform: str | None = None,
                     status: str | None = None,
                     keyword: str | None = None,
                     limit: int = Query(50, ge=1, le=500),
                     offset: int = Query(0, ge=0),
                     db: AsyncSession = Depends(get_db),
                     _: User = Depends(get_current_user)):
    """任务聚合列表（按平台/状态/关键词筛选，支持分页）。"""
    stmt = select(SrcTask)
    count_stmt = select(func.count()).select_from(SrcTask)
    if platform:
        stmt = stmt.where(SrcTask.platform == platform)
        count_stmt = count_stmt.where(SrcTask.platform == platform)
    if status:
        stmt = stmt.where(SrcTask.status == status)
        count_stmt = count_stmt.where(SrcTask.status == status)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(SrcTask.title.like(like))
        count_stmt = count_stmt.where(SrcTask.title.like(like))
    stmt = stmt.order_by(SrcTask.updated_at.desc()).limit(limit).offset(offset)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    return {"items": [SrcTaskOut.model_validate(r) for r in rows], "total": total}


@router.get("/stats")
async def task_stats(db: AsyncSession = Depends(get_db),
                     _: User = Depends(get_current_user)):
    """任务聚合统计：按平台、按状态分布与赏金区间上限合计。"""
    rows = (await db.execute(select(SrcTask))).scalars().all()
    by_platform: dict[str, int] = {}
    by_status: dict[str, int] = {}
    max_reward = 0.0
    for r in rows:
        by_platform[r.platform] = by_platform.get(r.platform, 0) + 1
        by_status[r.status] = by_status.get(r.status, 0) + 1
        max_reward += r.reward_max or 0.0
    return {
        "total": len(rows),
        "by_platform": by_platform,
        "by_status": by_status,
        "reward_max_total": round(max_reward, 2),
    }


@router.post("", response_model=SrcTaskOut)
async def create_task(req: SrcTaskCreate, db: AsyncSession = Depends(get_db),
                      user: User = Depends(require_role("admin", "analyst"))):
    """手工登记一条 SRC 任务。"""
    if not req.title.strip():
        raise HTTPException(400, "任务标题不能为空")
    task = SrcTask(**req.model_dump(), source="manual")
    db.add(task)
    await db.commit()
    await db.refresh(task)
    await audit.record(db, user, "src.task.create", task.title,
                       f"platform={task.platform} status={task.status}")
    return task


@router.post("/import")
async def import_tasks(req: SrcTaskImport, db: AsyncSession = Depends(get_db),
                       user: User = Depends(require_role("admin", "analyst"))):
    """批量导入任务：format=csv 或 json，返回导入/跳过统计。"""
    rows: list[dict] = []
    try:
        if req.format.lower() == "json":
            data = json.loads(req.content)
            items = data.get("items", data) if isinstance(data, dict) else data
            if isinstance(items, dict):
                items = [items]
            rows = [dict(i) for i in items if isinstance(i, dict)]
        else:
            reader = csv.DictReader(io.StringIO(req.content))
            rows = [dict(r) for r in reader]
    except (ValueError, TypeError) as exc:
        raise HTTPException(400, f"内容解析失败: {exc}")

    if not rows:
        raise HTTPException(400, "未解析到任何任务记录")

    imported = 0
    skipped = 0
    for raw in rows:
        title = str(raw.get("title", "")).strip()
        platform = str(raw.get("platform", "")).strip()
        if not title or not platform:
            skipped += 1
            continue
        dup = await db.execute(select(SrcTask).where(SrcTask.platform == platform,
                                                     SrcTask.title == title))
        if dup.scalar_one_or_none():
            skipped += 1
            continue
        db.add(SrcTask(
            platform=platform,
            title=title,
            status=str(raw.get("status", "open")).strip() or "open",
            reward_min=_parse_float(raw.get("reward_min")),
            reward_max=_parse_float(raw.get("reward_max")),
            currency=str(raw.get("currency", "CNY")).strip() or "CNY",
            scope=str(raw.get("scope", "")),
            url=str(raw.get("url", "")),
            description=str(raw.get("description", "")),
            deadline=_parse_deadline(raw.get("deadline")),
            source="import",
        ))
        imported += 1
    await db.commit()
    await audit.record(db, user, "src.task.import", f"{req.format}",
                       f"imported={imported} skipped={skipped}")
    return {"imported": imported, "skipped": skipped, "total": len(rows)}


@router.get("/{task_id}", response_model=SrcTaskOut)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db),
                   _: User = Depends(get_current_user)):
    task = await db.get(SrcTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    return task


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db),
                      user: User = Depends(require_role("admin"))):
    task = await db.get(SrcTask, task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    title = task.title
    await db.delete(task)
    await db.commit()
    await audit.record(db, user, "src.task.delete", title, "")
    return {"ok": True}
