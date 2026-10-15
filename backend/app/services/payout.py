"""收益结算口径：收益明细汇总与可提现余额计算。

余额口径（站内记账，不涉及真实资金划转）：
    可提现余额 = Σ(status=available 的收益) - Σ(未驳回的提现申请金额)
    累计收益   = Σ(全部收益)
    待结算     = Σ(status=pending 的收益)
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Earning, Withdrawal


async def summary(db: AsyncSession, user_id: int | None = None) -> dict:
    """按用户（user_id=None 表示全站）汇总收益与提现数据。"""
    e_where = [] if user_id is None else [Earning.user_id == user_id]
    w_where = [] if user_id is None else [Withdrawal.user_id == user_id]
    earnings = (await db.execute(select(Earning).where(*e_where))).scalars().all()
    withdrawals = (await db.execute(select(Withdrawal).where(*w_where))).scalars().all()

    total = sum(e.amount or 0.0 for e in earnings)
    pending = sum(e.amount or 0.0 for e in earnings if e.status == "pending")
    available = sum(e.amount or 0.0 for e in earnings if e.status == "available")
    withdrawn = sum(e.amount or 0.0 for e in earnings if e.status == "withdrawn")

    reserved = sum(w.amount or 0.0 for w in withdrawals
                   if w.status in ("pending", "approved", "paid"))

    by_platform: dict[str, float] = {}
    by_month: dict[str, float] = {}
    for e in earnings:
        by_platform[e.platform or "未知"] = by_platform.get(e.platform or "未知", 0.0) + (e.amount or 0.0)
        month = e.created_at.strftime("%Y-%m") if e.created_at else "未知"
        by_month[month] = by_month.get(month, 0.0) + (e.amount or 0.0)

    return {
        "total": round(total, 2),
        "pending": round(pending, 2),
        "available": round(available, 2),
        "withdrawn": round(withdrawn, 2),
        "reserved": round(reserved, 2),
        "withdrawable": round(max(available - reserved, 0.0), 2),
        "by_platform": {k: round(v, 2) for k, v in by_platform.items()},
        "by_month": dict(sorted(by_month.items())),
    }
