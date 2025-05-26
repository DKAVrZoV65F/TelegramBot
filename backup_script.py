from bs4 import BeautifulSoup
from aiogram.types import Message, Chat, User
from datetime import datetime
from handlers.collector import collect
import asyncio

CHAT_ID = -1


def make_fake_msg(message_id: int, username: str, user_id: int, date: datetime, text: str):
    return Message(
        message_id=message_id,
        date=date,
        chat=Chat(id=CHAT_ID, type="supergroup"),
        from_user=User(id=user_id, is_bot=False, username=username),
        text=text
    )


def parse_html_messages(html_path: str):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    msgs = []
    message_blocks = soup.select(".message.default")

    for i, block in enumerate(message_blocks, start=1):
        try:
            author_tag = block.select_one(".from_name")
            username = author_tag.text.strip() if author_tag else "anonymous"
            user_id = abs(hash(username)) % 10 ** 9

            text_tag = block.select_one(".text")
            text = text_tag.text.strip() if text_tag else ""

            date_tag = block.select_one(".pull_right.date")
            date_str = date_tag["title"]
            date = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S UTC%z")
            timestamp = int(date.timestamp())

            msg = make_fake_msg(i, username, user_id, timestamp, text)
            msgs.append(msg)
        except Exception as e:
            print(f"[!] Ошибка при обработке сообщения {i}: {e}")

    return msgs


async def main():
    messages = parse_html_messages("messages.html")
    for msg in messages:
        await collect(msg)


asyncio.run(main())
