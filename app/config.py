import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "HEMS Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # MongoDB
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "HEMS")

    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # External AI Service
    AI_SERVICE_URL: str = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
    AI_SERVICE_TIMEOUT: int = 30

    # Alert Thresholds
    WARNING_THRESHOLD: float = 0.2  # 20%
    CRITICAL_THRESHOLD: float = 0.1  # 10%
    FINAL_THRESHOLD: float = 0.05  # 5%

    class Config:
        case_sensitive = True


settings = Settings()
