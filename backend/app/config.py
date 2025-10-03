import os

class Settings:
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
    APP_NAME: str = "AI-in-a-Box API"
    VERSION: str = "0.4.0"

settings = Settings()
