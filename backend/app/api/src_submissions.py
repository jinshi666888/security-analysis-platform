"""SRC 漏洞提交追踪：登记、状态流转（时间线）、关联 finding、收益入账。"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.config import settings
from app.database import get_db
from app.models import Earning, Project, SrcSubmission, SrcTask, User
from app.schemas.src_submission import (SrcSubmissionCreate, SrcSubmissionFromFinding,
                                        SrcSubmissionOut, SrcSubmissionUpdate)
from app.services import audit, findings_reader, notify

router = APIRouter(prefix="/src/submissions", tags=["src-submissions"])

# 终态：审核通过/已发放赏金时触发收益入账
_EARNING_STATUSES = ("accepted", "paid")


def _timeline_append(raw: str, status: str, note: str) -> str:
    try:
        items = json.loads(raw) if raw else []
    except ValueError:
        items = []
    items.append({"time": datetime.utcnow().isoformat(timespec="seconds"),
                  "status": status, "note": note})
    return json.dumps(items, ensure_ascii=False)


def _to_out(row: SrcSubmission) -> SrcSubmissionOut:
    data = {c.name: getattr(row, c.name) for c in row.__table__.columns}
    try:
        data["timeline"] = json.loads(row.timeline) if row.timeline else []
    except ValueError:
        data["timeline"] = []
    return SrcSubmissionOut.model_validate(data)


async def _upsert_earning(db: AsyncSession, sub: SrcSubmission) -> None:
    """提交通过/发放赏金时，为提交人入账（幂等：按 submission_id 复用）。"""
    result = await db.execute(select(Earning).where(Earning.submission_id == sub.id))
    earning = result.scalar_one_or_none()
    if earning:
        earning.amount = sub.reward_amount
        earning.status = "available"
        earning.platform = sub.platform
    else:
        earning = Earning(user_id=sub.created_by, submission_id=sub.id,
                          platform=sub.platform, amount=sub.reward_amount,
                          status="available",
                          remark=f"SRC 提交 #{sub.id} 赏金入账")
        db.add(earning)
    await db.commit()
    if sub.reward_amount > 0:
        await notify.push(db, sub.created_by, "earning", "赏金已入账",
                          f"提交「{sub.title}」赏金 ¥{sub.reward_amount:.2f} 已计入可提现余额。")


@router.get("")
async def list_submissions(status: str | None = None,
                           platform: str | None = None,
                           project_id: int | None = None,
                           task_id: int | None = None,
                           keyword: str | None = None,
                           limit: int = Query(50, ge=1, le=500),
                           offset: int = Query(0, ge=0),
                           db: AsyncSession = Depends(get_db),
                           _: User = Depends(get_current_user)):
    """提交进度列表（按状态/平台/项目/任务筛选，支持分页）。"""
    stmt = select(SrcSubmission)
    count_stmt = select(func.count()).select_from(SrcSubmission)
    conds = []
    if status:
        conds.append(SrcSubmission.status == status)
    if platform:
        conds.append(SrcSubmission.platform == platform)
    if project_id:
        conds.append(SrcSubmission.project_id == project_id)
    if task_id:
        conds.append(SrcSubmission.task_id == task_id)
    if keyword:
        conds.append(SrcSubmission.title.like(f"%{keyword}%"))
    for c in conds:
        stmt = stmt.where(c)
        count_stmt = count_stmt.where(c)
    stmt = stmt.order_by(SrcSubmission.updated_at.desc()).limit(limit).offset(offset)

    rows = (await db.execute(stmt)).scalars().all()
    total = (await db.execute(count_stmt)).scalar_one()
    return {"items": [_to_out(r) for r in rows], "total": total}


@router.get("/stats")
async def submission_stats(db: AsyncSession = Depends(get_db),
                           _: User = Depends(get_current_user)):
    """提交进度统计：按状态分布、通过数与已确认赏金合计。"""
    rows = (await db.execute(select(SrcSubmission))).scalars().all()
    by_status: dict[str, int] = {}
    reward_total = 0.0
    for r in rows:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        if r.status in _EARNING_STATUSES:
            reward_total += r.reward_amount or 0.0
    return {"total": len(rows), "by_status": by_status,
            "accepted": by_status.get("accepted", 0) + by_status.get("paid", 0),
            "reward_total": round(reward_total, 2)}


@router.post("", response_model=SrcSubmissionOut)
async def create_submission(req: SrcSubmissionCreate, db: AsyncSession = Depends(get_db),
                            user: User = Depends(require_role("admin", "analyst"))):
    """手工登记一条 SRC 提交（可关联任务与本地 finding）。"""
    if not req.title.strip():
        raise HTTPException(400, "提交标题不能为空")
    if req.task_id:
        task = await db.get(SrcTask, req.task_id)
        if not task:
            raise HTTPException(400, "关联任务不存在")
    status = req.status or "draft"
    sub = SrcSubmission(
        **req.model_dump(exclude={"status"}),
        status=status,
        created_by=user.id,
        submitted_at=datetime.utcnow() if status != "draft" else None,
        timeline=_timeline_append("[]", status, "登记提交"),
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    await audit.record(db, user, "src.submission.create", sub.title,
                       f"platform={sub.platform} status={sub.status}")
    return _to_out(sub)


@router.post("/from-finding")
async def create_from_finding(req: SrcSubmissionFromFinding,
                              db: AsyncSession = Depends(get_db),
                              user: User = Depends(require_role("admin", "analyst"))):
    """从本地 confirmed 漏洞一键登记为 SRC 提交。"""
    project = await db.get(Project, req.project_id)
    if not project:
        raise HTTPException(404, "项目不存在")
    out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    finding = findings_reader.get_finding(out_dir, req.finding_id)
    if not finding:
        raise HTTPException(404, "漏洞不存在")
    if finding.get("status") != "confirmed":
        raise HTTPException(400, f"仅 confirmed 漏洞可登记，当前状态: {finding.get('status') or '空'}")

    dup = await db.execute(select(SrcSubmission).where(
        SrcSubmission.project_id == req.project_id,
        SrcSubmission.finding_id == req.finding_id))
    if dup.scalar_one_or_none():
        raise HTTPException(400, "该漏洞已登记过 SRC 提交")

    platform = req.platform
    if not platform and req.task_id:
        task = await db.get(SrcTask, req.task_id)
        platform = task.platform if task else ""

    title = f"[{finding.get('severity', 'medium')}] {finding.get('type') or '漏洞'} @ {finding.get('file', '')}"
    sub = SrcSubmission(
        task_id=req.task_id, project_id=req.project_id, finding_id=req.finding_id,
        title=title, platform=platform, severity=finding.get("severity", "medium"),
        status="draft", asset=finding.get("file", ""),
        vuln_type=finding.get("type", ""), note=req.note, created_by=user.id,
        timeline=_timeline_append("[]", "draft", f"由漏洞 {req.finding_id} 登记"),
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    await audit.record(db, user, "src.submission.from_finding", sub.title,
                       f"project={project.name} finding={req.finding_id}")
    return _to_out(sub)


@router.get("/{submission_id}", response_model=SrcSubmissionOut)
async def get_submission(submission_id: int, db: AsyncSession = Depends(get_db),
                         _: User = Depends(get_current_user)):
    sub = await db.get(SrcSubmission, submission_id)
    if not sub:
        raise HTTPException(404, "提交不存在")
    return _to_out(sub)


@router.put("/{submission_id}", response_model=SrcSubmissionOut)
async def update_submission(submission_id: int, req: SrcSubmissionUpdate,
                            db: AsyncSession = Depends(get_db),
                            user: User = Depends(require_role("admin", "analyst"))):
    """更新提交状态/赏金/备注，状态变更写入时间线并触发收益与通知。"""
    sub = await db.get(SrcSubmission, submission_id)
    if not sub:
        raise HTTPException(404, "提交不存在")
    if req.status is not None:
        if req.status != sub.status:
            sub.status = req.status
            sub.timeline = _timeline_append(sub.timeline, req.status, req.note or "状态变更")
            if req.status == "submitted" and not sub.submitted_at:
                sub.submitted_at = datetime.utcnow()
            if req.status in ("accepted", "rejected", "duplicate", "paid"):
                sub.resolved_at = datetime.utcnow()
        else:
            sub.timeline = _timeline_append(sub.timeline, sub.status, req.note or "更新备注")
    if req.reward_amount is not None:
        sub.reward_amount = req.reward_amount
    if req.note:
        sub.note = req.note
    await db.commit()
    await db.refresh(sub)

    if sub.status in _EARNING_STATUSES:
        await _upsert_earning(db, sub)
    await notify.push(db, sub.created_by, "submission", "提交状态更新",
                      f"提交「{sub.title}」当前状态：{sub.status}")
    await audit.record(db, user, "src.submission.update", sub.title,
                       f"status={sub.status} reward={sub.reward_amount}")
    return _to_out(sub)
