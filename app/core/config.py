from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str
    backend_url: str
    stripe_secret_key: str
    stripe_webhook_secret: str
    stripe_pro_price_id: str
    stripe_enterprise_price_id: str

    class Config:
        env_file = BASE_DIR / ".env"

settings = Settings()