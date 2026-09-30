import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    database_url = os.getenv("DATABASE_URL", "sqlite:///./fitbuddy.db")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    workout_model = os.getenv("GEMINI_WORKOUT_MODEL", "gemini-3.1-pro-preview")
    tip_model = os.getenv("GEMINI_TIP_MODEL", "gemini-3.8-flash")
    admin_password = os.getenv("ADMIN_PASSWORD", "change-me")
    session_secret = os.getenv("SESSION_SECRET", "change-this-to-a-long-random-secret")
    gemini_temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
    gemini_max_output_tokens = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "5000"))


settings = Settings()