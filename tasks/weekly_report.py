# tasks/weekly_report.py

import asyncio
import logging

from aiogram import Bot, types
from utils.config import settings
from handlers.statistics import (
    fetch_stats_data_from_db,
    fetch_tag_trends_data,
    fetch_top_n_tags,
)
from charts.chart_utils import generate_pie_chart, generate_line_chart

logger = logging.getLogger(__name__)


async def send_weekly_statistics_report(bot: Bot, admin_id: int, period_days: int = 7):
    logger.info(f"Начало формирования еженедельного отчета для admin_id: {admin_id} за {period_days} дней.")

    report_parts = [f"📊 Еженедельный статистический отчет (за последние {period_days} дней):\n"]
    photos_to_send = []

    try:
        stats_data_pie = await fetch_stats_data_from_db(period_days)
        positive_data_pie = stats_data_pie.get("positive")
        negative_data_pie = stats_data_pie.get("negative")

        if positive_data_pie:
            title = f"Позитивные упоминания (пирог, {period_days}д)"
            buffer = generate_pie_chart(positive_data_pie, title)
            if buffer:
                photos_to_send.append((types.InputFile(buffer, filename=f"weekly_positive_pie.png"), title))
        else:
            report_parts.append("▫️ Нет данных для пирога позитивной статистики.")

        if negative_data_pie:
            title = f"Негативные упоминания (пирог, {period_days}д)"
            buffer = generate_pie_chart(negative_data_pie, title)
            if buffer:
                photos_to_send.append((types.InputFile(buffer, filename=f"weekly_negative_pie.png"), title))
        else:
            report_parts.append("▫️ Нет данных для пирога негативной статистики.")

        tag_trends_data = await fetch_tag_trends_data(period_days)
        if tag_trends_data:
            title = f"Динамика упоминаний тегов (тренды, {period_days}д)"
            buffer = generate_line_chart(tag_trends_data, title)
            if buffer:
                photos_to_send.append((types.InputFile(buffer, filename=f"weekly_tag_trends.png"), title))
            else:
                report_parts.append("▫️ Не удалось сгенерировать график трендов (нет данных для отображения).")
        else:
            report_parts.append("▫️ Нет данных для графика трендов.")

        top_n_tags_data = await fetch_top_n_tags(period_days, top_n=5)
        top_tags_text_parts = []
        if top_n_tags_data.get("positive"):
            positive_top_list = "\n".join([f"  - {tag} ({count})" for tag, count in top_n_tags_data["positive"]])
            top_tags_text_parts.append(
                f"👍 Топ-{len(top_n_tags_data['positive'])} позитивных тегов:\n{positive_top_list}")

        if top_n_tags_data.get("negative"):
            negative_top_list = "\n".join([f"  - {tag} ({count})" for tag, count in top_n_tags_data["negative"]])
            top_tags_text_parts.append(
                f"👎 Топ-{len(top_n_tags_data['negative'])} негативных тегов:\n{negative_top_list}")

        if top_tags_text_parts:
            report_parts.append("\n" + "\n\n".join(top_tags_text_parts))
        else:
            report_parts.append("▫️ Нет данных по топ-N тегам.")

        if len(report_parts) > 1 or not photos_to_send:
            await bot.send_message(admin_id, "\n".join(report_parts))
        elif len(report_parts) == 1 and photos_to_send:
            await bot.send_message(admin_id, report_parts[0])

        for photo_file, caption_text in photos_to_send:
            try:
                await bot.send_photo(admin_id, photo_file, caption=caption_text)
            except Exception as e_photo:
                logger.error(f"Не удалось отправить фото для еженедельного отчета admin_id {admin_id}: {e_photo}")
                await bot.send_message(admin_id, f"Не удалось отправить график: {caption_text}")
            await asyncio.sleep(0.3)

        logger.info(f"Еженедельный отчет успешно отправлен admin_id: {admin_id}")

    except Exception as e:
        logger.exception(f"Ошибка при формировании еженедельного отчета для admin_id {admin_id}:")
        try:
            await bot.send_message(admin_id, f"Произошла ошибка при формировании еженедельного отчета: {e}")
        except Exception as e_send_err:
            logger.error(
                f"Не удалось отправить сообщение об ошибке еженедельного отчета admin_id {admin_id}: {e_send_err}")


async def trigger_weekly_report(bot: Bot):
    logger.info("[TASK] Weekly report task STARTED")
    for admin_id in settings.ADMIN_IDS:
        await send_weekly_statistics_report(bot, admin_id, period_days=7)
        await asyncio.sleep(1)
