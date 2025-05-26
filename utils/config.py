# config.py

from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


@dataclass
class Settings:
    TG_TOKEN: str = os.getenv("TG_TOKEN", "")
    ADMIN_IDS: list[int] = field(default_factory=lambda:
    [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x])
    DB_PATH: Path = Path(os.getenv("DB_PATH", DATA_DIR / "bot.fdb"))
    HF_CACHE: Path = Path(os.getenv("HF_HOME", BASE_DIR / "hf_cache"))

    DB_USER: str = os.getenv("DB_USER", "sysdba")
    DB_PASS: str = os.getenv("DB_PASS", "masterkey")
    DB_CHARSET: str = "UTF8"

    DAILY_REPORT_HOUR: int = int(os.getenv("DAILY_REPORT_HOUR", 20))
    DAILY_REPORT_MINUTE: int = int(os.getenv("DAILY_REPORT_MINUTE", 0))

    WEEKLY_REPORT_HOUR: int = int(os.getenv("WEEKLY_REPORT_HOUR", 20))
    WEEKLY_REPORT_MINUTE: int = int(os.getenv("WEEKLY_REPORT_MINUTE", 0))

    TIMEZONE_STR: str = os.getenv("TIMEZONE", "Europe/Moscow")


settings = Settings()

if not settings.TG_TOKEN:
    raise RuntimeError("TG_TOKEN не найден, заполните .env")
