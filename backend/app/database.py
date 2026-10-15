"""SQLAlchemy 异步连接与会话管理。"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    from app.models import User
    from sqlalchemy import select

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "admin"))
        if not result.scalar_one_or_none():
            admin = User(username="admin", role="admin", is_active=True)
            admin.set_password("admin123")
            session.add(admin)
            analyst = User(username="analyst", role="analyst", is_active=True)
            analyst.set_password("analyst123")
            session.add(analyst)
            dev = User(username="developer", role="developer", is_active=True)
            dev.set_password("dev123")
            session.add(dev)
            await session.commit()

    await _seed_src_tasks()


async def _seed_src_tasks():
    """首次启动时写入少量示例 SRC 任务，便于任务聚合与提交流程演示。"""
    from app.models import SrcTask
    from sqlalchemy import select

    async with AsyncSessionLocal() as session:
        existing = (await session.execute(select(SrcTask).limit(1))).scalar_one_or_none()
        if existing:
            return
        session.add_all([
            SrcTask(platform="补天", title="某电商平台 双十一活动众测", status="open",
                    reward_min=500, reward_max=5000, scope="*.example-shop.com 及 App",
                    description="重点：支付逻辑、越权、SQL 注入；禁止破坏数据。", source="manual"),
            SrcTask(platform="漏洞盒子", title="某政务云平台专项众测", status="open",
                    reward_min=1000, reward_max=10000, scope="gov.example.com 授权域名",
                    description="重点：越权、SSRF、敏感信息泄露。", source="manual"),
            SrcTask(platform="教育SRC", title="高校统一认证系统测试", status="in_progress",
                    reward_min=200, reward_max=2000, scope="认证系统测试账号",
                    description="重点：逻辑漏洞、越权、认证绕过。", source="manual"),
            SrcTask(platform="HackerOne", title="Open Source SaaS Bug Bounty", status="open",
                    reward_min=100, reward_max=3000, currency="USD", scope="*.saas-example.io",
                    description="Focus: IDOR, SSRF, auth bypass.", source="manual"),
        ])
        await session.commit()
