import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LLM_PROVIDER: str = "gemini"
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"

    MOCK_FINANCE_BASE_URL: str = "http://127.0.0.1:8000/finance/"
    PLAYWRIGHT_HEADLESS: bool = True

    APPROVAL_THRESHOLD_INR: float = 100000.0
    MAX_AGENT_STEPS: int = 15
    MAX_RETRIES: int = 3

    # Computed paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    INVOICES_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "invoices"
    SCREENSHOTS_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "screenshots"
    DATABASE_PATH: Path = Path(__file__).resolve().parent.parent / "data" / "taskpilot.db"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.INVOICES_DIR.mkdir(parents=True, exist_ok=True)
settings.SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
settings.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
