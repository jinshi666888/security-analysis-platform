from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.database import get_db
from app.models import AuditLog, User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def list_audit(action: str | None = None,
                     limit: int = Query(100, ge=1, le=500),
                     offset: int = Query(0, ge=0),
                     db: AsyncSession = Depends(get_db),
                     _: User = Depends(require_role("admin"))):
    """操作审计日志（M10，仅管理员可见）。"""
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
        count_stmt = count_stmt.where(AuditLog.action == action)
    stmt = stmt.order_by(AuditLog.id.desc()).limit(limit).offset(offset)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    names = {u.id: u.username for u in (await db.execute(select(User))).scalars().all()}

    return {
        "items": [{
            "id": r.id,
            "user_id": r.user_id,
            "username": names.get(r.user_id, "匿名"),
            "action": r.action,
            "target": r.target,
            "detail": r.detail,
            "created_at": r.created_at,
        } for r in rows],
        "total": total,
    }
