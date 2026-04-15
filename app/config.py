from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")


class Settings:
    APP_NAME = "Global Geopolitics, War and Crime News Tracker"
    APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
    APP_PORT = int(os.getenv("APP_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
    NEWSAPI_BASE_URL = "https://newsapi.org/v2/everything"
    USE_RSS_FALLBACK = os.getenv("USE_RSS_FALLBACK", "true").lower() == "true"

    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

    DAILY_SUMMARY_HOUR = int(os.getenv("DAILY_SUMMARY_HOUR", "8"))
    DAILY_SUMMARY_MINUTE = int(os.getenv("DAILY_SUMMARY_MINUTE", "0"))
    DEFAULT_LOOKBACK_HOURS = int(os.getenv("DEFAULT_LOOKBACK_HOURS", "36"))
    MAX_ARTICLES_PER_TOPIC = int(os.getenv("MAX_ARTICLES_PER_TOPIC", "12"))

    DATABASE_PATH = str(DATA_DIR / "news_tracker.db")


settings = Settings()
