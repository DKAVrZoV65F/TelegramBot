# handlers/tag_actions.py

from aiogram import types
from config import settings
from db import get_conn
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

ADMIN_IDS = settings.ADMIN_IDS


async def process_mark(call: types.CallbackQuery):
  try:
    _, action, chat_id, msg_id, tag = call.data.split(":")
    action, chat_id, msg_id = map(int, (action, chat_id, msg_id))
  except ValueError:
    return await call.answer("Ошибка формата!")

  if call.from_user.id not in ADMIN_IDS:
    return await call.answer("⛔ Нет прав")

  con = get_conn()
  cur = con.cursor()
  cur.execute("""
    SELECT processed FROM message_tags
    WHERE message_id=? AND chat_id=? AND tag_id=(
      SELECT id FROM tags WHERE name=?
    )
  """, (msg_id, chat_id, tag))

  if not cur.fetchone():
    con.close()
    return await call.answer("Тег не найден!")

  cur.execute("""
    UPDATE message_tags
    SET processed = ?
    WHERE message_id=? AND chat_id=? AND tag_id=(
      SELECT id FROM tags WHERE name=?
    )
  """, (action, msg_id, chat_id, tag))

  cur.execute("""
    INSERT INTO tag_actions(message_id,chat_id,tag_id,action,action_by)
    VALUES ( ?,?, (SELECT id FROM tags WHERE name=?), ?, ? )
  """, (msg_id, chat_id, tag,
     'approved' if action else 'rejected',
     call.from_user.username or "admin"))

  cur.execute("""
    UPDATE messages
    SET tagged = ?
    WHERE id=? AND chat_id=?
  """, (1 if action else -1, msg_id, chat_id))

  con.commit()
  con.close()

  badge = "✅" if action else "❌"
  text_user = call.from_user.username or ""
  kb = InlineKeyboardMarkup(row_width=1)
  kb.add(InlineKeyboardButton(f"{badge} {text_user}", callback_data="noop"))
  kb.add(InlineKeyboardButton("🗑 Закрыть", callback_data="close_notify"))

  await call.message.edit_reply_markup(kb)
  await call.answer("Сохранено!")

def register(dp):
  dp.register_callback_query_handler(process_mark, lambda c: c.data.startswith("mark:"))
  dp.register_callback_query_handler(lambda c: c.answer(), lambda c: c.data=="noop")
