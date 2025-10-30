import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017/hems")
    MONGO_URI: str = os.getenv("MONGO_URI")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "mysecretkey")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    AI_AGENT_URL: str = os.getenv("AI_AGENT_URL", "http://localhost:9000/analyze")

settings = Settings()
print(settings.JWT_SECRET)