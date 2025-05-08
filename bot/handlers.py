# handlers.py
import json, asyncio
from datetime import datetime
from aiogram import Dispatcher, types

from .db import get_connection
from .ai import keyword_tagger


def register(dp: Dispatcher):
    @dp.message_handler(content_types=types.ContentType.ANY)
    async def collect(message: types.Message):
        await save_to_db(message)
        tags = await keyword_tagger(message.text or "")
        await save_tags(message, tags)
        if tags:
            await message.reply(f"🏷 {', '.join(tags)}")


async def save_to_db(m: types.Message):
    con = get_connection()
    cur = con.cursor()
    cur.execute("""
        INSERT INTO messages
          (id, chat_id, user_id, username, msg_date, text, raw_json, tagged)
        VALUES (?,?,?,?,?,?,?,0)
        """, 
        (
            m.message_id,
            m.chat.id,
            m.from_user.id if m.from_user else None,
            m.from_user.username if m.from_user else None,
            datetime.utcfromtimestamp(m.date.timestamp()),
            m.text or '',
            json.dumps(m.to_python()),
        ),
    )
    con.commit()
    con.close()


async def save_tags(m: types.Message, tags: list[str]):
    if not tags:
        return

    con = get_connection()
    cur = con.cursor()

    for tag in tags:
        cur.execute(
            "UPDATE OR INSERT INTO tags (name) VALUES (?) MATCHING (name)", (tag,)
        )
        cur.execute("SELECT id FROM tags WHERE name=?", (tag,))
        tag_id = cur.fetchone()[0]

        cur.execute(
            """
            SELECT 1 FROM message_tags
            WHERE message_id=? AND chat_id=? AND tag_id=?
            """,
            (m.message_id, m.chat.id, tag_id),
        )
        if cur.fetchone():
            continue

        cur.execute(
            """
            INSERT INTO message_tags (message_id, chat_id, tag_id)
            VALUES (?,?,?)
            """,
            (m.message_id, m.chat.id, tag_id),
        )

    cur.execute(
        "UPDATE messages SET tagged=1 WHERE id=? AND chat_id=?",
        (m.message_id, m.chat.id),
    )
    con.commit()
    con.close()
