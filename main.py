# main.py

from asyncio.log import logger
import logging, sys
from aiogram import Bot, Dispatcher, executor
from config import settings
from handlers import register_handlers
from tasks import daily_report
from tasks.daily_report import setup_scheduler
from tasks.weekly_report import trigger_weekly_report

logging.basicConfig(level=logging.INFO,
          stream=sys.stdout,
          format="%(asctime)s | %(levelname)s | %(name)s: %(message)s")

bot = Bot(settings.TG_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

register_handlers(dp)

def setup_schedulers(bot_instance: Bot):
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from zoneinfo import ZoneInfo

    try:
        tz = ZoneInfo(settings.TIMEZONE_STR)
    except Exception:
        logger.warning(f"Не удалось загрузить таймзону {settings.TIMEZONE_STR} из zoneinfo, пробуем pytz или UTC.")
        try:
            from pytz import timezone
            tz = timezone(settings.TIMEZONE_STR)
        except Exception:
            logger.error(f"Не удалось установить таймзону {settings.TIMEZONE_STR}. Используется UTC.")
            tz = None

    scheduler = AsyncIOScheduler(timezone=tz)

    if hasattr(settings, 'DAILY_REPORT_HOUR') and hasattr(settings, 'DAILY_REPORT_MINUTE'):
        scheduler.add_job(
            daily_report._build_and_send,
            trigger=CronTrigger(
                day_of_week='mon-sun', # Каждый день
                hour=settings.DAILY_REPORT_HOUR,
                minute=settings.DAILY_REPORT_MINUTE,
                timezone=tz
            ),
            args=(bot_instance,),
            id="daily_report_job",
            replace_existing=True
        )
        logger.info(f"Ежедневный отчет запланирован на {settings.DAILY_REPORT_HOUR}:{settings.DAILY_REPORT_MINUTE} ({settings.TIMEZONE_STR}).")

    if hasattr(settings, 'WEEKLY_REPORT_HOUR') and hasattr(settings, 'WEEKLY_REPORT_MINUTE'):
        scheduler.add_job(
            trigger_weekly_report,
            trigger=CronTrigger(
                day_of_week='fri',  # Пятница (mon,tue,wed,thu,fri,sat,sun или 0-6)
                hour=settings.WEEKLY_REPORT_HOUR,
                minute=settings.WEEKLY_REPORT_MINUTE,
                timezone=tz
            ),
            args=(bot_instance,),
            id="weekly_statistics_report_job",
            replace_existing=True
        )
        logger.info(f"Еженедельный статистический отчет запланирован на пятницу {settings.WEEKLY_REPORT_HOUR}:{settings.WEEKLY_REPORT_MINUTE} ({settings.TIMEZONE_STR}).")
    else:
        logger.warning("Время для еженедельного отчета не настроено в settings (WEEKLY_REPORT_HOUR, WEEKLY_REPORT_MINUTE).")


    scheduler.start()
    logger.info("Планировщик задач запущен.")


async def on_startup(dp):
  setup_schedulers(bot)

def main():
  logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s | %(levelname)s | %(name)s | %(module)s:%(lineno)d | %(message)s"
    )
  print("[BOT] running …")
  executor.start_polling(
    dp,
    skip_updates=True,
    on_startup=on_startup
  )

if __name__ == "__main__":
  main()
