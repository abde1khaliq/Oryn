from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str
    backend_url: str

    class Config:
        env_file = BASE_DIR / ".env"

settings = Settings()