"""操作审计：统一写入 audit_logs 表。

设计原则：审计写入失败不得影响主业务流程，因此所有异常均被吞掉并回滚。
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog, User


async def record(db: AsyncSession, user: User | None, action: str,
                 target: str = "", detail: str = "") -> None:
    """记录一条审计日志（user=None 表示匿名/未认证主体）。"""
    try:
        db.add(AuditLog(
            user_id=user.id if user else 0,
            action=action,
            target=str(target)[:250],
            detail=str(detail)[:2000],
        ))
        await db.commit()
    except Exception:  # noqa: BLE001 - 审计失败不影响业务
        await db.rollback()
