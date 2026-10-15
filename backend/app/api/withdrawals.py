"""提现管理：申请 → 审核（批准/驳回）→ 打款，状态流转触发站内通知。"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.database import get_db
from app.models import User, Withdrawal
from app.schemas.withdrawal import WithdrawalCreate, WithdrawalOut, WithdrawalReview
from app.services import audit, notify, payout

router = APIRouter(prefix="/withdrawals", tags=["withdrawals"])

_METHOD_TEXT = {"alipay": "支付宝", "wechat": "微信", "bank": "银行卡"}


@router.get("")
async def list_withdrawals(status: str | None = None,
                           all_users: bool = False,
                           limit: int = Query(50, ge=1, le=500),
                           offset: int = Query(0, ge=0),
                           db: AsyncSession = Depends(get_db),
                           user: User = Depends(get_current_user)):
    """提现申请列表（默认仅本人；管理员可查看全站）。"""
    uid = None if (user.role == "admin" and all_users) else user.id
    stmt = select(Withdrawal)
    count_stmt = select(func.count()).select_from(Withdrawal)
    conds = [] if uid is None else [Withdrawal.user_id == uid]
    if status:
        conds.append(Withdrawal.status == status)
    for c in conds:
        stmt = stmt.where(c)
        count_stmt = count_stmt.where(c)
    stmt = stmt.order_by(Withdrawal.created_at.desc()).limit(limit).offset(offset)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    names = {u.id: u.username for u in (await db.execute(select(User))).scalars().all()}
    items = []
    for r in rows:
        data = WithdrawalOut.model_validate(r).model_dump()
        data["username"] = names.get(r.user_id, "匿名")
        items.append(data)
    return {"items": items, "total": total}


@router.post("", response_model=WithdrawalOut)
async def create_withdrawal(req: WithdrawalCreate, db: AsyncSession = Depends(get_db),
                            user: User = Depends(require_role("admin", "analyst"))):
    """提交提现申请，校验金额不超过当前可提现余额。"""
    if req.amount <= 0:
        raise HTTPException(400, "提现金额必须大于 0")
    acct = await payout.summary(db, user.id)
    if req.amount > acct["withdrawable"]:
        raise HTTPException(400, f"可提现余额不足，当前可提现 ¥{acct['withdrawable']:.2f}")
    wd = Withdrawal(user_id=user.id, amount=req.amount, method=req.method,
                    account=req.account, status="pending")
    db.add(wd)
    await db.commit()
    await db.refresh(wd)
    await notify.push(db, user.id, "withdrawal", "提现申请已提交",
                      f"提现 ¥{req.amount:.2f}（{_METHOD_TEXT.get(req.method, req.method)}）已提交，等待审核。")
    await audit.record(db, user, "withdrawal.create", f"wd#{wd.id}",
                       f"amount={wd.amount} method={wd.method}")
    return wd


@router.post("/{wd_id}/review", response_model=WithdrawalOut)
async def review_withdrawal(wd_id: int, req: WithdrawalReview,
                            db: AsyncSession = Depends(get_db),
                            user: User = Depends(require_role("admin"))):
    """审核提现申请：decision=approve 批准 / reject 驳回。"""
    wd = await db.get(Withdrawal, wd_id)
    if not wd:
        raise HTTPException(404, "提现申请不存在")
    if wd.status != "pending":
        raise HTTPException(400, f"当前状态不可审核: {wd.status}")
    if req.decision not in ("approve", "reject"):
        raise HTTPException(400, "decision 必须为 approve 或 reject")
    wd.status = "approved" if req.decision == "approve" else "rejected"
    wd.reviewer_id = user.id
    wd.review_note = req.note
    wd.reviewed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(wd)
    text = "已批准，等待打款" if wd.status == "approved" else "已驳回"
    await notify.push(db, wd.user_id, "withdrawal", f"提现申请{text}",
                      f"提现 ¥{wd.amount:.2f} {text}。{('备注：' + req.note) if req.note else ''}")
    await audit.record(db, user, "withdrawal.review", f"wd#{wd.id}",
                       f"decision={req.decision} note={req.note}")
    return wd


@router.post("/{wd_id}/pay", response_model=WithdrawalOut)
async def pay_withdrawal(wd_id: int, db: AsyncSession = Depends(get_db),
                         user: User = Depends(require_role("admin"))):
    """标记提现已打款（站内记账，不触发真实资金划转）。"""
    wd = await db.get(Withdrawal, wd_id)
    if not wd:
        raise HTTPException(404, "提现申请不存在")
    if wd.status != "approved":
        raise HTTPException(400, f"仅已批准的申请可打款，当前状态: {wd.status}")
    wd.status = "paid"
    wd.paid_at = datetime.utcnow()
    await db.commit()
    await db.refresh(wd)
    await notify.push(db, wd.user_id, "withdrawal", "提现已打款",
                      f"提现 ¥{wd.amount:.2f} 已打款至 {_METHOD_TEXT.get(wd.method, wd.method)} {wd.account}。")
    await audit.record(db, user, "withdrawal.pay", f"wd#{wd.id}", f"amount={wd.amount}")
    return wd
