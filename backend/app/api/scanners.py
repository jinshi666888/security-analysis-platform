from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.config import settings
from app.models import User
from app.services.scanner import probe_scanners

router = APIRouter(prefix="/scanners", tags=["scanners"])


@router.get("")
async def list_scanners(_: User = Depends(get_current_user)):
    """扫描器可用性探测（对应 runtime `list-scanners`，供 M6 扫描配置可视化）。"""
    if not (Path(settings.runtime_path) / "main.py").is_file():
        raise HTTPException(500, f"runtime 不存在: {settings.runtime_path}")
    try:
        return await probe_scanners()
    except RuntimeError as exc:
        raise HTTPException(500, str(exc))
