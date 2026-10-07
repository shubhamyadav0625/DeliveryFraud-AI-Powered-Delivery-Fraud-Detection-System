import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "DeliveryFraud — AI-Powered Delivery Fraud Detection System"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "delivery_fraud_super_secret_jwt_key_2026_change_in_prod")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "sqlite:///./delivery_fraud.db"
    )

    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

    model_config = SettingsConfigDict(case_sensitive=True)

settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
