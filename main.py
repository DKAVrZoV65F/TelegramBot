# main.py

import logging, sys
from aiogram import Bot, Dispatcher, executor
from config import settings
from handlers import register_handlers
from tasks.daily_report import setup_scheduler

logging.basicConfig(level=logging.INFO,
          stream=sys.stdout,
          format="%(asctime)s | %(levelname)s | %(name)s: %(message)s")

bot = Bot(settings.TG_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

register_handlers(dp)

async def on_startup(dp):
  setup_scheduler(bot)

def main():
  print("[BOT] running …")
  executor.start_polling(
    dp,
    skip_updates=True,
    on_startup=on_startup
  )

if __name__ == "__main__":
  main()
