from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "CTI-NLP Threat Dashboard API"
    DATABASE_URL: str = "sqlite:///./cti_dashboard.db" # Change to postgresql://user:pass@host/db for prod
    SECRET_KEY: str = "your-super-secret-jwt-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    OPENAI_API_KEY: str = ""
    VIRUSTOTAL_API_KEY: str = ""
    ABUSEIPDB_API_KEY: str = ""
    FRONTEND_URLS: str = "http://localhost:3000"  # Comma-separated list of allowed origins

    class Config:
        env_file = ".env"

settings = Settings()