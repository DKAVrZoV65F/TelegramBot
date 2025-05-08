# db.py
from pathlib import Path
from typing import Union
import firebird.driver

from .config import settings, BASE_DIR

DDL_FILE = BASE_DIR / "database" / "ddl.sql"


def _dsn(path: Union[str, Path]) -> str:
    """
    host:path   или   абсолютный_путь
    """
    path_str = str(Path(path).expanduser()).replace("\\", "/")
    return f"{settings.DB_HOST}:{path_str}" if settings.DB_HOST else path_str


def _create_db_if_not_exists() -> None:
    if settings.DB_HOST:
        return

    db_path = Path(settings.DB_PATH).expanduser()
    if db_path.exists():
        return

    print(f"[DB] Creating Firebird database at {db_path}")

    con = firebird.driver.create_database(
        _dsn(db_path),
        user=settings.DB_USER,
        password=settings.DB_PASS,
        charset=settings.DB_CHARSET,
    )

    with open(DDL_FILE, encoding="utf-8") as ddl:
        sql = ddl.read()
    cur = con.cursor()
    for stmt in filter(None, (s.strip() for s in sql.split(";"))):
        cur.execute(stmt)
    con.commit()
    con.close()
    print("[DB] Schema installed.")


def get_connection() -> firebird.driver.Connection:
    _create_db_if_not_exists()
    return firebird.driver.connect(
        _dsn(settings.DB_PATH),
        user=settings.DB_USER,
        password=settings.DB_PASS,
        charset=settings.DB_CHARSET,
    )