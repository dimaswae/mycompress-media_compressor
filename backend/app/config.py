from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "mycompress"
    debug: bool = True
    api_prefix: str = "/api/v1"
    upload_max_size_mb: int = 100
    storage_dir: str = "storage"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    db_url: str = "sqlite:///./mycompress.db"
    db_echo: bool = False
    job_ttl_hours: int = 24
    storage_quota_gb: int = 5
    ffmpeg_timeout_seconds: int = 120
    sweep_interval_minutes: int = 60

    model_config = {"env_prefix": "MYCOMPRESS_", "env_file": ".env"}


settings = Settings()
