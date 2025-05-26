# tasks/daily_report.py

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from db import get_conn
from config import settings
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import types
from apscheduler.triggers.date import DateTrigger

async def _build_and_send(bot):
    print("[TASK] Daily report task STARTED")
    since = datetime.utcnow() - timedelta(days=1)
    con = get_conn(); cur = con.cursor()

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

def setup_scheduler(bot):
    tz = ZoneInfo("Europe/Moscow")
    sched = AsyncIOScheduler(timezone=tz)
    run_date = datetime.now(tz).replace(hour=settings.HOUR, minute=settings.MINUTE, second=0, microsecond=0)

    sched.add_job(
        _build_and_send,
        trigger=DateTrigger(run_date=run_date),
        args=(bot,),
        id="daily_report",
        replace_existing=True
    )

    sched.start()
