from fastapi import APIRouter

from app.api import (audit, auth, earnings, findings, knowledge, notifications,
                     projects, review, scans, scanners, src_submissions, src_tasks,
                     users, withdrawals)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(scans.router)
api_router.include_router(scanners.router)
api_router.include_router(findings.router)
api_router.include_router(review.router)
api_router.include_router(users.router)
api_router.include_router(audit.router)
api_router.include_router(src_tasks.router)
api_router.include_router(src_submissions.router)
api_router.include_router(earnings.router)
api_router.include_router(withdrawals.router)
api_router.include_router(notifications.router)
api_router.include_router(knowledge.router)
