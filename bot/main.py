# main.py
import asyncio, logging, sys
from aiogram import Bot, Dispatcher
from aiogram.utils import executor

from .config import settings
from .handlers import register

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

if not settings.TG_TOKEN:
    raise RuntimeError("TG_TOKEN не найден. Заполните .env.")
    
bot = Bot(token=settings.TG_TOKEN, parse_mode="HTML")
dp  = Dispatcher(bot)
register(dp)


def start():
    print("[BOT] Starting …")
    executor.start_polling(dp, skip_updates=True)


if __name__ == "__main__":
    start()
