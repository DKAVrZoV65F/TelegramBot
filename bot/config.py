# config.py
from pathlib import Path
from dataclasses import dataclass
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass 

BASE_DIR   = Path(__file__).resolve().parent.parent
DATA_DIR   = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

@dataclass
class Settings:
    TG_TOKEN: str      = os.getenv("TG_TOKEN", "")
    DB_HOST:  str = os.getenv("DB_HOST", "")
    DB_PATH: Path      = Path(os.getenv("DB_PATH", DATA_DIR / ""))
    DB_USER:  str = os.getenv("DB_USER", "sysdba")
    DB_PASS:  str = os.getenv("DB_PASS", "masterkey")
    DB_CHARSET: str = "UTF8"

settings = Settings()