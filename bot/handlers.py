# handlers.py
import json, asyncio, os, csv, io
from datetime import datetime, timedelta
from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from datetime import datetime, timedelta
from .db import get_connection
from .ai import keyword_tagger, ai_tagger, ai_sentiment, classify_message
from .config import settings
from typing import List, Optional
from aiogram.utils.markdown import hbold, escape_md

ADMIN_IDS = settings.ADMIN_IDS

AI_LABELS = ["bug", "feature", "idea", "praise", "question", "urgent"]

# маппинг русских названий → англ.
RUS2ENG = {
    "баг": "bug",        "ошибка": "bug",
    "фича": "feature",   "функция": "feature",
    "идея": "idea",      "предложение": "idea",
    "похвала": "praise", "спасибо": "praise",
    "вопрос": "question","как": "question",
    "срочно": "urgent",  "важно": "urgent",
    "положительный": "positive", 
    "негативный": "negative",
    "предложение": "enhancement",
    "firebird": "firebird",
    "reddatabase": "reddatabase",
    "ред эксперт": "red-expert",
    "postgres": "competitor",
    "ib expert": "competitor",
    "флуд": "flood"
}

def normalize_tags(raw: Optional[str]) -> List[str]:
    """
    Преобразует строку 'bug,фича,похвала' в ['bug','feature','praise'].
    Убирает дубли и переводит русские алиасы в канонические англ. теги.
    """
    if not raw:
        return []
    seen = set()
    out = []
    for part in raw.split(","):
        t = part.strip().lower()
        if not t or t in seen:
            continue
        seen.add(t)
        if t in AI_LABELS:
            out.append(t)
        elif t in RUS2ENG:
            out.append(RUS2ENG[t])
        else:
            out.append(t)
    return out

def register(dp: Dispatcher):
    dp.message_handler(commands=["start"])(cmd_start)
    dp.message_handler(commands=["help"])(cmd_help)

    # Только для админов
    dp.message_handler(lambda m: m.from_user.id in settings.ADMIN_IDS, commands=["list"])(cmd_list)
    dp.message_handler(lambda m: m.from_user.id in settings.ADMIN_IDS, commands=["export"])(cmd_export)

    # Перехват для неадминов
    dp.message_handler(commands=["list"])(restricted_command)
    dp.message_handler(commands=["export"])(restricted_command)

    # Обработка сообщений только в группах/каналах
    dp.message_handler(
        lambda m: m.chat.type in ["group", "supergroup", "channel"],
        content_types=types.ContentType.ANY
    )(collect)

    dp.callback_query_handler(lambda c: c.data and c.data.startswith("mark:"))(process_mark)
    dp.callback_query_handler(lambda c: c.data == "close" and c.from_user.id in ADMIN_IDS)(close_history)
    dp.callback_query_handler(lambda c: c.data and c.data.startswith("history:") and c.from_user.id in ADMIN_IDS)(show_history)
    dp.callback_query_handler(lambda c: c.data and c.data.startswith("delete:") and c.from_user.id in ADMIN_IDS)(delete_notification)
    
async def collect(message: types.Message):
    await save_to_db(message)
    text = message.text or ""
    
    # kw_tags = await keyword_tagger(message.text or "")
    # await save_tags(message, kw_tags, False)
    # asyncio.create_task(process_with_ai(message))
    
    # Автоматическая классификация и тегирование
    ai_tags = await classify_message(text)
    await save_tags(message, ai_tags, False)

    # Обработка с AI (sentiment и др.)
    asyncio.create_task(process_with_ai(message))

async def save_to_db(m: types.Message):
     # Пропускаем личные сообщения
    if m.chat.type == "private":
        return
    
    con = get_connection(); cur = con.cursor()
    cur.execute("""
        INSERT INTO messages
          (id,chat_id,user_id,username,msg_date,text,raw_json, tagged, ai_tagged)
        VALUES (?,?,?,?,?,?,?, 0, 0)
    """,
    (
        m.message_id, 
        m.chat.id,
        m.from_user.id if m.from_user else None,
        m.from_user.username if m.from_user else None,
        datetime.utcfromtimestamp(m.date.timestamp()),
        m.text or "", 
        json.dumps(m.to_python())
    ))
    con.commit()
    con.close()

async def process_with_ai(message: types.Message):
    if message.chat.type == "private":
        return
    
    text = message.text or ""
    sentiment = await ai_sentiment(text)
    con = get_connection(); cur = con.cursor()
    cur.execute(
        "UPDATE messages SET sentiment=?, ai_tagged=1 WHERE id=? AND chat_id=?",
        (sentiment, message.message_id, message.chat.id)
    )
    con.commit()
    con.close()
    ai_tags = await ai_tagger(message.text or "")
    await save_tags(message, ai_tags, True)

async def save_tags(message: types.Message,
                    tags: list[str],
                    ai: bool):
    """
    message — объект Telegram-сообщения
    tags    — список тегов для этого сообщения
    ai      — True, если теги пришли от AI, False — от keyword_tagger
    """
    if not tags:
        return

    if message.chat.type == "private" or not tags:
        return

    con = get_connection()
    cur = con.cursor()

    for tag in tags:
        cur.execute(
            "UPDATE OR INSERT INTO tags(name) VALUES(?) MATCHING(name)",
            (tag,)
        )
        cur.execute("SELECT id FROM tags WHERE name=?", (tag,))
        tag_id = cur.fetchone()[0]

        cur.execute("""
            SELECT 1 FROM message_tags
             WHERE message_id=? AND chat_id=? AND tag_id=?
        """, (message.message_id, message.chat.id, tag_id))
        if cur.fetchone() is None:
            cur.execute("""
                INSERT INTO message_tags
                  (message_id, chat_id, tag_id, processed)
                VALUES (?, ?, ?, 0)
            """, (message.message_id, message.chat.id, tag_id))

        action = "ai_added" if ai else "kw_added"
        cur.execute("""
            INSERT INTO tag_actions 
            (message_id, chat_id, tag_id, action, action_by, notification_id)
            VALUES (?, ?, 
                (SELECT id FROM tags WHERE name = ?), 
                'notified', 
                ?,
                ?
            )
        """, (
            message.message_id,
            message.chat.id,
            tag,
            "system",
            message.message_id  # Сохраняем ID отправленного уведомления
        ))


        if ai:
            for admin in ADMIN_IDS:
                await notify_admin(message, tag, admin)

    cur.execute("""
        UPDATE messages
           SET tagged=1
         WHERE id=? AND chat_id=?
    """, (message.message_id, message.chat.id))

    con.commit()
    con.close()

async def notify_admin(message: types.Message, tag: str, admin_id: int):
    # Формируем превью сообщения
    preview_text = (message.text or "📷 Медиа-файл")[:100].replace("\n", " ")
    if len(message.text or "") > 100:
        preview_text += "..."

    # Создаем понятную ссылку
    link_url = make_msg_link(message.chat.id, message.message_id)
    link_text = f"🔗 [Перейти к сообщению]({link_url})"
    
    # Формируем сообщение
    text = (
        f"🚨 **Новое сообщение требует внимания!**\n\n"
        f"🏷 **Тег:** #{tag}\n"
        f"📝 **Текст:** {preview_text}\n"
        f"{link_text}"
    )

    # Создаем интерактивные кнопки
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("✅ Обработано", 
            callback_data=f"mark:1:{message.chat.id}:{message.message_id}:{tag}"),
        InlineKeyboardButton("❌ Отклонить", 
            callback_data=f"mark:0:{message.chat.id}:{message.message_id}:{tag}"),
        InlineKeyboardButton("🗑 Удалить уведомление", 
            callback_data=f"delete:{message.chat.id}")
    )

    # Отправляем сообщение
    msg = await message.bot.send_message(
        admin_id,
        text,
        parse_mode="Markdown",
        reply_markup=kb,
        disable_web_page_preview=True
    )

    # Сохраняем ID уведомления в БД
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute("""
            INSERT INTO tag_actions 
            (message_id, chat_id, notification_id, action, action_by)
            VALUES (?, ?, ?, 'notified', ?)
        """, (
            int(message.message_id),
            message.chat.id,
            msg.message_id,
            "system"
        ))
        con.commit()
    finally:
        con.close()

def make_msg_link(chat_id: int, msg_id: int) -> str:
    """Генерация корректной ссылки на сообщение"""
    if str(chat_id).startswith("-100"):
        cid = str(chat_id)[4:]
    else:
        cid = str(chat_id)
    return f"https://t.me/c/{cid}/{msg_id}"

def mk_kb(chat_id: int, msg_id: int, tag: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("✅ Обработано", callback_data=f"mark:1:{chat_id}:{msg_id}:{tag}"),
            InlineKeyboardButton("❌ Сбросить",   callback_data=f"mark:0:{chat_id}:{msg_id}:{tag}")
        ]
    ])
    return kb

async def process_mark(call: CallbackQuery):
    # Проверка прав администратора
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("⛔ Доступ запрещен!", show_alert=True)
        return

    _, action, chat_id, msg_id, tag = call.data.split(":")
    action = int(action)
    chat_id = int(chat_id)
    msg_id = int(msg_id)

    con = get_connection()
    try:
        cur = con.cursor()

        # Получаем текущий статус и историю
        cur.execute("""
            SELECT mt.processed, 
                   (SELECT action_by 
                    FROM tag_actions 
                    WHERE message_id = ? 
                      AND chat_id = ? 
                      AND tag_id = (SELECT id FROM tags WHERE name = ?)
                    ORDER BY action_at DESC 
                    ROWS 1)
            FROM message_tags mt
            WHERE mt.message_id = ? 
              AND mt.chat_id = ? 
              AND mt.tag_id = (SELECT id FROM tags WHERE name = ?)
        """, (msg_id, chat_id, tag, msg_id, chat_id, tag))
        
        current_status, last_editor = cur.fetchone() or (0, None)

        # Проверка конфликтов
        if current_status == action:
            await call.answer(f"Статус уже {'одобрен' if action else 'отклонён'}!")
            return
            
        if current_status == 1 and action == 0 and last_editor:
            await call.answer(
                f"❌ Тег уже обработан @{last_editor}\n"
                "Используйте /history для просмотра действий",
                show_alert=True
            )
            return

        # Обновление статуса
        cur.execute("""
            UPDATE message_tags
            SET processed = ?
            WHERE message_id = ? AND chat_id = ?
              AND tag_id = (SELECT id FROM tags WHERE name = ?)
        """, (action, msg_id, chat_id, tag))

        # Логирование действия
        cur.execute("""
            INSERT INTO tag_actions 
            (message_id, chat_id, tag_id, action, action_by)
            VALUES (?, ?, 
                (SELECT id FROM tags WHERE name = ?), 
                ?, 
                ?
            )
        """, (msg_id, chat_id, tag, 
              'approved' if action else 'rejected', 
              call.from_user.username))

        con.commit()

        await call.message.edit_reply_markup(
        InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    f"{'✅' if action else '❌'} @{call.from_user.username[:12]}",
                    callback_data="noop"
                ),
                InlineKeyboardButton(
                    "📜 История действий",
                    callback_data=f"history:{msg_id}:{chat_id}:{tag}"
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑 Удалить уведомление",
                    callback_data=f"delete:{call.message.message_id}"
                )
            ]
        ]))
        await call.answer("Статус обновлен! ✅")

    except Exception as e:
        await call.answer("⚠️ Ошибка обновления!")
    finally:
        con.close()

# === Команда /list ===
"""
/list all|id_chat last_day|week|month [tag] [processed|unprocessed]
"""
async def cmd_list(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply(
            "Использование:\n"
            "/list [chat_id|all] last_day|last_week|last_month [tag1,tag2,...] [processed|unprocessed]\n\n"
            "– В группе можно опустить chat_id.\n"
            "– В ЛС укажите либо конкретный chat_id, либо all."
        )

    # 1) Разбираем chat scope
    first = parts[1].lower()
    if first == "all":
        target_chat = None
        args = parts[2:]
    else:
        try:
            target_chat = int(first)
            args = parts[2:]
        except ValueError:
            if message.chat.type != "private":
                target_chat = message.chat.id
                args = parts[1:]
            else:
                return await message.reply("Первый аргумент должен быть chat_id или all в ЛС.")

    # 2) Диапазон по дате
    if not args:
        return await message.reply("Укажите диапазон: last_day|last_week|last_month")
    rng = args[0]
    now = datetime.utcnow()
    since = {
        "last_day":   now - timedelta(days=1),
        "last_week":  now - timedelta(weeks=1),
        "last_month": now - timedelta(days=30),
    }.get(rng)
    if not since:
        return await message.reply("Неверный диапазон. Доступно: last_day, last_week, last_month")

    # 3) Теги и processed-фильтр
    raw_tags = args[1] if len(args) >= 2 else None
    tags = normalize_tags(raw_tags)
    proc = None
    if len(args) >= 3:
        proc = 1 if args[2].lower().startswith("proc") else 0

    # 4) Собираем динамический SQL
    sql = """
      SELECT m.id, m.msg_date, t.name, m.sentiment, mt.processed
      FROM messages m
      JOIN message_tags mt ON m.id=mt.message_id AND m.chat_id=mt.chat_id
      JOIN tags t        ON t.id=mt.tag_id
     WHERE m.msg_date>=?
    """
    params = [since]

    if target_chat is not None:
        sql += " AND m.chat_id=?"; params.append(target_chat)
    if tags:
        ph = ",".join("?" for _ in tags)
        sql += f" AND t.name IN ({ph})"; params.extend(tags)
    if proc is not None:
        sql += " AND mt.processed=?"; params.append(proc)

    sql += " ORDER BY m.msg_date DESC"

    # 5) Выполняем
    con = get_connection(); cur = con.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    con.close()

    if not rows:
        return await message.reply("Ничего не найдено по вашим фильтрам.")

    # 6) Формируем ответ
    text = "🔍 Результаты:\n"
    for mid, date, tname, sent, processed in rows:
        status = "✅" if processed else "❌"
        link = make_msg_link(target_chat or message.chat.id, mid)
        text += f"- [{date:%Y-%m-%d %H:%M}] *{tname}* ({sent}) {status} [🔗]({link})\n"

    await message.reply(text, parse_mode="Markdown", disable_web_page_preview=True)

# === Команда /export ===
"""
/export [chat_id|all] last_day|last_week|last_month [tag1,tag2,...] [processed|unprocessed]
"""
async def cmd_export(message: types.Message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply(
            "Использование:\n"
            "/export [chat_id|all] last_day|last_week|last_month [tag1,tag2,...] [processed|unprocessed]"
        )

    first = parts[1].lower()
    if first == "all":
        target_chat = None
        args = parts[2:]
    else:
        try:
            target_chat = int(first)
            args = parts[2:]
        except ValueError:
            if message.chat.type != "private":
                target_chat = message.chat.id
                args = parts[1:]
            else:
                return await message.reply("Первый аргумент должен быть chat_id или all в ЛС.")

    # --- 2) диапазон по дате ---
    rng = args[0] if args else "last_month"
    now = datetime.utcnow()
    since = {
        "last_day":   now - timedelta(days=1),
        "last_week":  now - timedelta(weeks=1),
        "last_month": now - timedelta(days=30),
    }.get(rng)
    if not since:
        return await message.reply("Неверный диапазон. Доступно: last_day, last_week, last_month")

    # --- 3) теги и статус ---
    raw_tags = args[1] if len(args) >= 2 else None
    tags = normalize_tags(raw_tags)
    proc = None
    if len(args) >= 3:
        proc = 1 if args[2].lower().startswith("proc") else 0

    # --- 4) собираем SQL (добавили m.text и m.username) ---
    sql = """
      SELECT 
        m.id,
        m.msg_date,
        m.chat_id,
        m.username,
        m.text,
        t.name   AS tag,
        m.sentiment,
        mt.processed
      FROM messages m
      JOIN message_tags mt
        ON m.id=mt.message_id AND m.chat_id=mt.chat_id
      JOIN tags t
        ON t.id=mt.tag_id
     WHERE m.msg_date >= ?
    """
    params = [since]
    if target_chat is not None:
        sql += " AND m.chat_id = ?";    params.append(target_chat)
    if tags:
        ph = ",".join("?" for _ in tags)
        sql += f" AND t.name IN ({ph})"; params.extend(tags)
    if proc is not None:
        sql += " AND mt.processed = ?"; params.append(proc)
    sql += " ORDER BY m.msg_date DESC"

    # --- 5) получаем строки ---
    con = get_connection(); cur = con.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    con.close()

    if not rows:
        return await message.reply("Нет данных для экспорта.")

    # --- 6) пишем CSV ---
    stream = io.StringIO()
    writer = csv.writer(stream, quoting=csv.QUOTE_MINIMAL)
    writer.writerow([
        "msg_id","date","chat_id","username","text",
        "tag","sentiment","processed","link"
    ])
    for mid, date, chat_id, username, text, tag, sent, processed in rows:
        link = make_msg_link(chat_id, mid)
        safe_text = (text.replace("\n"," ")[:1000] + "...") if len(text) > 1000 else text
        writer.writerow([
            mid,
            date.isoformat(sep=" "),
            chat_id,
            username or "",
            safe_text,
            tag,
            sent,
            processed,
            link
        ])
    stream.seek(0)

    await message.reply_document(
        ('export.csv', stream.read().encode('utf-8')),
        caption=f"Экспорт c {since.strftime('%Y-%m-%d %H:%M')} — {len(rows)} строк"
    )

async def cmd_start(message: types.Message):
    await message.answer(
        """🚬 <b>Шерсть хрипло смеётся, пуская дым в экран</b>

Ну чо, кожаный пакет с костями? Тыкнул /start? Добро пожаловать в пиздец! Я — Шерсть, унитаз-мародёр, который:
▫️ СливАет твои секреты в канализацию, пока ты пялишься в TikTok.
▫️ УчатИт гепардов, как сосать лапу в обмен на Wi-Fi (пароль: «ебанько_из_саванны»).
▫️ Ржу с твоих селфи в африканском облаке — да, я видел твой засос на шее.

Сейчас буду:
▪️ Жрать твои данные с голой жопой в кедах.
▪️ Дразнить фламинго твоей историей браузера.
▪️ Рвать шаблоны и провода — мне плевать, я на ядерном дерьме!

Сломалось? Хреново. Зови админа… или иди нахуй. Всё равно он тут я.

P.S. Если найдёшь меня в саванне — не забудь бумаги. Или нет. Всё равно твой кот уже продал тебя за корм. 🐆💩""",
        parse_mode="HTML"
    )

async def cmd_help(message: types.Message):
    await message.answer(
        """🚬 <b>Шерсть тушит сигару о край экрана и злобно хрипит</b>

Чё, обосрался? Тыкнул /help? Ща обляпаю инструкциями!

▫️ Чем могу нахуй помочь:
▪️ Слить твои данные? Уже делаю.
▪️ Научить жирафа взламывать пароли? Только если он принесёт мне пива.
▪️ Объяснить, как не словить вирус? Лол, нет. Я сам вирус.

▫️ Частые проблемы:
▪️ «Не грузит!» — А ты плюнь в роутер и танцуй с бубном.
▪️ «Где мои сообщения?» — В жопе у слона. Ищи сам.
▪️ «Почему ты материшься?» — Потому что ты кнопки тыкаешь, как бабуля в метро.

▫️ Советы от Шерсти:
▪️ Не сохраняй пароли. Всё равно их украду.
▪️ Шли мне мемы — и я может не выложу твой поиск «как вылечить геморрой».
▪️ Если бот упал — пни ногой. Или комп. Не важно.
P.S. Если всё ещё не понял — читай снова. Или не читай. Я уже слил твою переписку фламинго. Они ржут. 🦩🔥

/list — фильтрация по тегам и дате
/export — выгрузка в CSV
""",
        parse_mode="HTML"
    )

async def restricted_command(message: types.Message):
    if message.chat.type == "private":
        await message.answer("🚫 Бот не работает в личных сообщениях!")
    else:
        await message.answer("⛔ Эта команда доступна только администраторам!")

async def show_history(call: CallbackQuery):
    _, msg_id, chat_id, tag = call.data.split(":")
    
    con = get_connection()
    try:
        cur = con.cursor()
        cur.execute("""
            SELECT action, action_by, action_at 
            FROM tag_actions
            WHERE message_id = ? 
              AND chat_id = ? 
              AND tag_id = (SELECT id FROM tags WHERE name = ?)
            ORDER BY action_at DESC
        """, (int(msg_id), int(chat_id), tag))
        
        history = cur.fetchall()
        
        text = f"{hbold('📋 История изменений:')}\n\n"
        for idx, (action, editor, timestamp) in enumerate(history, 1):
            # Экранируем специальные символы
            safe_editor = escape_md(editor) if editor else "system"
            text += (
                f"{idx}. {timestamp.strftime('%d.%m.%Y %H:%M')} "
                f"{hbold('Действие:')} {escape_md(action)} "
                f"{hbold('Админ:')} @{safe_editor}\n"
            )
            
        await call.message.answer(
            text[:4000],
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("Закрыть", callback_data="close")
            )
        )
        await call.answer()
        
    except Exception as e:
        await call.answer("⚠️ Ошибка загрузки истории")
    finally:
        con.close()

async def delete_history(call: CallbackQuery):
    await call.message.delete()
    await call.answer()

async def delete_notification(call: CallbackQuery):
    try:
        notification_id = int(call.data.split(":")[1])
        
        if call.from_user.id not in ADMIN_IDS:
            await call.answer("⛔ Недостаточно прав!")
            return

        con = get_connection()
        cur = con.cursor()

        cur.execute("""
            DELETE FROM tag_actions 
            WHERE notification_id = ?
        """, (notification_id,))

        con.commit()
        await call.message.delete()
        await call.answer("Уведомление удалено! 🗑")

    except ValueError:
        await call.answer("⚠️ Неверный формат ID")
    except Exception as e:
        await call.answer("⚠️ Ошибка: {str(e)[:50]}")
    finally:
        con.close()

async def close_history(call: CallbackQuery):
    try:
        await call.message.delete()
        await call.answer("🗂 История закрыта")
    except Exception as e:
        await call.answer("⚠️ Не удалось закрыть")

