from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "mycompress"
    debug: bool = True
    api_prefix: str = "/api/v1"
    upload_max_size_mb: int = 100
    storage_dir: str = "storage"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = {"env_prefix": "MYCOMPRESS_", "env_file": ".env"}


settings = Settings()
