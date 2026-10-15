from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.database import get_db
from app.models import User
from app.schemas.auth import UserCreate, UserOut, UserUpdate
from app.services import audit

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(db: AsyncSession = Depends(get_db),
                     _: User = Depends(require_role("admin"))):
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()


@router.post("", response_model=UserOut)
async def create_user(req: UserCreate, db: AsyncSession = Depends(get_db),
                      actor: User = Depends(require_role("admin"))):
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none():
        raise HTTPException(400, "用户名已存在")
    user = User(username=req.username, role=req.role, is_active=True)
    user.set_password(req.password)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await audit.record(db, actor, "user.create", user.username, f"role={user.role}")
    return user


@router.put("/{user_id}", response_model=UserOut)
async def update_user(user_id: int, req: UserUpdate, db: AsyncSession = Depends(get_db),
                      actor: User = Depends(require_role("admin"))):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    changes = []
    if req.password:
        user.set_password(req.password)
        changes.append("password")
    if req.role is not None:
        user.role = req.role
        changes.append(f"role={req.role}")
    if req.is_active is not None:
        user.is_active = req.is_active
        changes.append(f"is_active={req.is_active}")
    await db.commit()
    await db.refresh(user)
    await audit.record(db, actor, "user.update", user.username, ",".join(changes))
    return user


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db),
                      actor: User = Depends(require_role("admin"))):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "用户不存在")
    if user.id == actor.id:
        raise HTTPException(400, "不能删除当前登录用户")
    name = user.username
    await db.delete(user)
    await db.commit()
    await audit.record(db, actor, "user.delete", name, "")
    return {"ok": True}
