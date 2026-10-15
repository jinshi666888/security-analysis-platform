"""应用配置：环境变量驱动，零配置可启动。"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SAP_", extra="ignore")

    app_name: str = "Security Analysis Platform"
    secret_key: str = "dev-secret-change-in-production-32chars!!"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    database_url: str = "sqlite+aiosqlite:///./app.db"

    runtime_path: str = r"G:\SecurityValidation\pkg\security-analysis-project\security-analysis-runtime"
    python_exe: str = r"C:\Users\Administrator\.workbuddy\binaries\python\versions\3.13.12\python.exe"
    default_out_root: str = r"G:\SecurityValidation\platform_data"


settings = Settings()
