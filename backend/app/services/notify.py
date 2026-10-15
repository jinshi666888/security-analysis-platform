"""站内通知：收益/提现/提交状态变更统一推送。
与审计一致，通知写入失败不得阻断主业务流程。
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification


async def push(db: AsyncSession, user_id: int, category: str, title: str,
               content: str = "") -> None:
    """写入一条站内通知（失败静默回滚）。"""
    try:
        db.add(Notification(user_id=user_id, category=category,
                            title=title[:200], content=content[:2000]))
        await db.commit()
    except Exception:  # noqa: BLE001 - 通知失败不影响业务
        await db.rollback()
