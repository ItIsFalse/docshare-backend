import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # App
    APP_NAME = os.getenv("APP_NAME", "DocShare")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost/docshare")

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-me")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # Email
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")


settings = Settings()