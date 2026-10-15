"""收益管理：收益明细与统计（按平台/月份），支持余额口径查询。"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models import Earning, User
from app.schemas.earning import EarningCreate, EarningOut
from app.services import audit, payout

router = APIRouter(prefix="/earnings", tags=["earnings"])


def _scope(user: User, all_users: bool) -> int | None:
    """管理员可查看全站（all_users=true），其余仅本人数据。"""
    if user.role == "admin" and all_users:
        return None
    return user.id


@router.get("")
async def list_earnings(platform: str | None = None,
                        status: str | None = None,
                        all_users: bool = False,
                        limit: int = Query(50, ge=1, le=500),
                        offset: int = Query(0, ge=0),
                        db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    """收益明细列表（默认仅本人；管理员可查看全站）。"""
    uid = _scope(user, all_users)
    stmt = select(Earning)
    count_stmt = select(func.count()).select_from(Earning)
    conds = [] if uid is None else [Earning.user_id == uid]
    if platform:
        conds.append(Earning.platform == platform)
    if status:
        conds.append(Earning.status == status)
    for c in conds:
        stmt = stmt.where(c)
        count_stmt = count_stmt.where(c)
    stmt = stmt.order_by(Earning.created_at.desc()).limit(limit).offset(offset)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    return {"items": [EarningOut.model_validate(r) for r in rows], "total": total}


@router.get("/summary")
async def earning_summary(all_users: bool = False,
                          db: AsyncSession = Depends(get_db),
                          user: User = Depends(get_current_user)):
    """收益统计：累计/待结算/可提现/按平台/按月份。"""
    return await payout.summary(db, _scope(user, all_users))


@router.post("", response_model=EarningOut)
async def create_earning(req: EarningCreate, db: AsyncSession = Depends(get_db),
                         user: User = Depends(require_role("admin", "analyst"))):
    """手工补录一条收益（如平台直接打款到账）。"""
    earning = Earning(user_id=user.id, **req.model_dump())
    db.add(earning)
    await db.commit()
    await db.refresh(earning)
    await audit.record(db, user, "earning.create", f"earning#{earning.id}",
                       f"amount={earning.amount} platform={earning.platform}")
    return earning
