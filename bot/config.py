# config.py
from pathlib import Path
from dataclasses import dataclass, field
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
    HF_CACHE_DIR: Path = Path(os.getenv("HF_HOME", BASE_DIR / "hf_cache"))
    TG_TOKEN: str      = os.getenv("TG_TOKEN", "")
    ADMIN_IDS: list[int] = field(default_factory=lambda: [
        int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
    ])
    DB_HOST:  str = os.getenv("DB_HOST", "")
    DB_PATH: Path      = Path(os.getenv("DB_PATH", DATA_DIR / ""))
    DB_USER:  str = os.getenv("DB_USER", "sysdba")
    DB_PASS:  str = os.getenv("DB_PASS", "masterkey")
    DB_CHARSET: str = "UTF8"

settings = Settings()
