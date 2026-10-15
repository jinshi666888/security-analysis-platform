"""站内通知：列表、未读数、标记已读。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Notification, User
from app.schemas.notification import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _uid(user: User, all_users: bool) -> int | None:
    if user.role == "admin" and all_users:
        return None
    return user.id


@router.get("")
async def list_notifications(category: str | None = None,
                             unread_only: bool = False,
                             all_users: bool = False,
                             limit: int = Query(50, ge=1, le=500),
                             offset: int = Query(0, ge=0),
                             db: AsyncSession = Depends(get_db),
                             user: User = Depends(get_current_user)):
    """通知列表（默认仅本人，支持只看未读）。"""
    uid = _uid(user, all_users)
    stmt = select(Notification)
    count_stmt = select(func.count()).select_from(Notification)
    conds = [] if uid is None else [Notification.user_id == uid]
    if category:
        conds.append(Notification.category == category)
    if unread_only:
        conds.append(Notification.is_read.is_(False))
    for c in conds:
        stmt = stmt.where(c)
        count_stmt = count_stmt.where(c)
    stmt = stmt.order_by(Notification.created_at.desc()).limit(limit).offset(offset)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    return {"items": [NotificationOut.model_validate(r) for r in rows], "total": total}


@router.get("/unread-count")
async def unread_count(db: AsyncSession = Depends(get_db),
                       user: User = Depends(get_current_user)):
    """当前用户未读通知数（用于菜单角标）。"""
    stmt = select(func.count()).select_from(Notification).where(
        Notification.user_id == user.id, Notification.is_read.is_(False))
    return {"unread": (await db.execute(stmt)).scalar_one()}


@router.post("/{notification_id}/read")
async def mark_read(notification_id: int, db: AsyncSession = Depends(get_db),
                    user: User = Depends(get_current_user)):
    """标记单条通知为已读（仅本人）。"""
    note = await db.get(Notification, notification_id)
    if not note:
        raise HTTPException(404, "通知不存在")
    if note.user_id != user.id and user.role != "admin":
        raise HTTPException(403, "权限不足")
    note.is_read = True
    await db.commit()
    return {"ok": True}


@router.post("/read-all")
async def mark_all_read(db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    """一键全部已读（仅本人）。"""
    await db.execute(update(Notification).where(
        Notification.user_id == user.id, Notification.is_read.is_(False)).values(is_read=True))
    await db.commit()
    return {"ok": True}
