from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import create_token, get_current_user
from app.database import get_db
from app.models import User
from app.schemas.auth import LoginRequest, Token, UserOut
from app.services import audit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if not user or not user.verify_password(req.password):
        await audit.record(db, None, "auth.login.failed", req.username, "用户名或密码错误")
        raise HTTPException(401, "用户名或密码错误")
    if not user.is_active:
        await audit.record(db, user, "auth.login.failed", req.username, "账号已禁用")
        raise HTTPException(401, "账号已禁用")
    await audit.record(db, user, "auth.login", req.username, f"role={user.role}")
    return Token(access_token=create_token(user), role=user.role, username=user.username)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user
