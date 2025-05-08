from bot import version
from bot.db import get_connection

def test_version():
    assert version() == "0.1.0"

def test_db_auto_create(tmp_path, monkeypatch):
    # Подменяем путь, чтобы не трогать real-базу
    from bot import config
    fake_db = tmp_path / "fake.fdb"
    monkeypatch.setattr(config.settings, "DB_PATH", fake_db)

    con = get_connection()
    cur = con.cursor()
    # Таблица messages должна существовать
    cur.execute("SELECT rdb$relation_name FROM rdb$relations WHERE rdb$relation_name='MESSAGES'")
    assert cur.fetchone() is not None
    con.close()