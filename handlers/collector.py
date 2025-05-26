# handlers/collector.py

from aiogram import types
from ai import classify_with_scores
from utils import enough_chars
from db import get_conn
from datetime import datetime
from ai import classify_sentiment, classify_theme

TARGET = {"вопросы", "баги", "фичи", "конкуренты"}

async def collect(msg: types.Message):

  if msg.chat.type not in ("group", "supergroup", "channel"):
    return

  if not enough_chars(msg.text):
    return
  
  themes = await classify_theme(msg.text or "")
  relevant_tags = [tag for tag in themes if tag in TARGET]
  scores = await classify_with_scores(msg.text or "")

  if not relevant_tags:
    return

  main_tag = relevant_tags[0]
  tags = [main_tag]
  sent = await classify_sentiment(msg.text or "")

  print("Tags:", tags)
  print("Scores:", scores)
  print("Selected tag:", relevant_tags)

  con = get_conn()
  cur = con.cursor()
  cur.execute("""
  UPDATE OR INSERT INTO messages(id, chat_id, user_id, username, msg_date, text, sentiment)
  VALUES (?, ?, ?, ?, ?, ?, ?)
  MATCHING(id, chat_id)
  """, (
    msg.message_id,
    msg.chat.id,
    msg.from_user.id if msg.from_user else None,
    msg.from_user.username if msg.from_user else None,
    datetime.utcfromtimestamp(msg.date.timestamp()),
    msg.text or "",
    sent,
  ))

  for tag in tags:
    cur.execute("UPDATE OR INSERT INTO tags(name) VALUES(?) MATCHING(name)", (tag,))
    cur.execute("SELECT id FROM tags WHERE name=?", (tag,))
    tag_id = cur.fetchone()[0]
    cur.execute("""
      MERGE INTO message_tags mt
      USING (
        SELECT ? AS message_id, ? AS chat_id, ? AS tag_id FROM rdb$database
      ) vals
      ON (
        mt.message_id = vals.message_id AND
        mt.chat_id = vals.chat_id AND
        mt.tag_id = vals.tag_id
      )
      WHEN NOT MATCHED THEN
        INSERT (message_id, chat_id, tag_id, processed)
        VALUES (vals.message_id, vals.chat_id, vals.tag_id, 0);
    """, (msg.message_id, msg.chat.id, tag_id))

  con.commit()
  con.close()

def register(dp):
  dp.register_message_handler(collect, content_types=types.ContentType.ANY)
