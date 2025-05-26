# tasks/daily_report.py

from datetime import datetime, timedelta
from db import get_conn
from utils.config import settings
from aiogram import types


async def build_and_send(bot):
    print("[TASK] Daily report task STARTED")
    since = datetime.utcnow() - timedelta(days=1)
    con = get_conn()
    cur = con.cursor()

    cur.execute("""
        SELECT COUNT(DISTINCT m.id)
        FROM messages m
        JOIN message_tags mt
        ON m.id = mt.message_id AND m.chat_id = mt.chat_id
        WHERE m.msg_date >= ?
        AND (mt.processed IS NULL OR mt.processed = 0)
    """, (since,))
    total = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(DISTINCT id) FROM messages WHERE sentiment='positive' AND msg_date>=?", (since,))
    positive = cur.fetchone()[0] or 0
    cur.execute("SELECT COUNT(DISTINCT id) FROM messages WHERE sentiment='negative' AND msg_date>=?", (since,))
    negative = cur.fetchone()[0] or 0
    con.close()

    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(
        text=f"📨 Показать",
        callback_data=f"u:day"
    ))
    text = (
        f"📊 Ежедневный отчёт (последние 24 ч):\n"
        f"• Всего сообщений: {total}\n"
        f"• Позитивных:      {positive}\n"
        f"• Негативных:      {negative}"
    )
    for admin_id in settings.ADMIN_IDS:
        await bot.send_message(admin_id, text, reply_markup=kb)
