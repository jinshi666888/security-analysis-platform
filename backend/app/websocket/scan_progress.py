"""WebSocket 扫描进度推送。"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

STAGES = ["inventory", "scan", "normalize", "context", "taint", "triage", "output"]

STAGE_FILES = {
    "inventory": "inventory.json",
    "scan": "scans",
    "normalize": "scans",
    "context": "context.json",
    "taint": "taint-findings.json",
    "triage": "triage/triage.json",
    "output": "findings.json",
}


@router.websocket("/ws/scan/{project_id}")
async def scan_progress_ws(websocket: WebSocket, project_id: int):
    await websocket.accept()
    out_dir = None
    try:
        from app.config import settings
        from app.database import AsyncSessionLocal
        from app.models import Project

        async with AsyncSessionLocal() as session:
            project = await session.get(Project, project_id)
            if project:
                out_dir = project.out_dir or str(Path(settings.default_out_root) / project.name)
    except Exception:
        pass

    if not out_dir:
        await websocket.send_json({"error": "项目不存在"})
        await websocket.close()
        return

    out_path = Path(out_dir)
    current = 0
    try:
        while current < len(STAGES):
            stage = STAGES[current]
            await websocket.send_json({"stage": stage, "status": "running",
                                       "progress": current / len(STAGES)})
            target = out_path / STAGE_FILES[stage]
            waited = 0
            while not target.exists() and waited < 300:
                await asyncio.sleep(0.5)
                waited += 0.5
            await websocket.send_json({"stage": stage, "status": "done",
                                       "progress": (current + 1) / len(STAGES)})
            current += 1
        await websocket.send_json({"stage": "all", "status": "completed", "progress": 1.0})
    except WebSocketDisconnect:
        pass
