from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    secret_key: str = "change-me-in-production"
    database_url: str = "sqlite+aiosqlite:///./nivpro.db"
    upload_dir: Path = Path("./uploads")
    images_dir: Path = Path("./uploads/images")
    allow_registration: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


def get_settings() -> Settings:
    return Settings()
