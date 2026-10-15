from __future__ import annotations

from passlib.context import CryptContext
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="analyst")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    def set_password(self, raw: str) -> None:
        self.hashed_password = pwd_context.hash(raw)

    def verify_password(self, raw: str) -> bool:
        return pwd_context.verify(raw, self.hashed_password)
