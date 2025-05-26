# db/__init__.py

from pathlib import Path
from firebird.driver import connect, create_database
from config import settings, BASE_DIR


DDL_FILE = BASE_DIR / "db" / "ddl.sql"
DDL_SQL = DDL_FILE.read_text(encoding="utf-8")
  

def _dsn(path: Path) -> str:
  return str(path).replace("\\", "/")


def _init_schema():
  if settings.DB_PATH.exists():
    return

  print(f"[DB] creating {settings.DB_PATH}")
  con = create_database(
    _dsn(settings.DB_PATH),
    user=settings.DB_USER,
    password=settings.DB_PASS,
    charset=settings.DB_CHARSET
  )

  cur = con.cursor()
  for stmt in filter(None, (s.strip() for s in DDL_SQL.split(";"))):
    cur.execute(stmt)

  con.commit()
  con.close()
  print("[DB] schema installed")
  

def get_conn():
  _init_schema()
  return connect(
    _dsn(settings.DB_PATH),
    user=settings.DB_USER,
    password=settings.DB_PASS,
    charset=settings.DB_CHARSET
  )
