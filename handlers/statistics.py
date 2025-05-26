# handlers/statistics.py

from aiogram import types
import logging
from db import get_conn
from charts.chart_utils import generate_line_chart, generate_pie_chart
from datetime import datetime, timedelta
from keyboards.statistics_keyboards import period_menu, statistics_type_menu


async def cmd_statistics(message: types.Message):
    await message.answer("📊 Статистика. Выберите тип отчета:",
                         reply_markup=statistics_type_menu())


async def fetch_stats_data_from_db(days: int):
    since_date = datetime.utcnow() - timedelta(days=days)
    conn = get_conn()
    cur = conn.cursor()

    sql_corrected = """
        SELECT
            m.sentiment,
            t.name AS tag_name,
            COUNT(*) AS tag_count 
        FROM messages m
        INNER JOIN message_tags mt ON m.id = mt.message_id AND m.chat_id = mt.chat_id
        INNER JOIN tags t ON mt.tag_id = t.id
        WHERE m.msg_date >= ? AND m.sentiment IN ('positive', 'negative')
        GROUP BY m.sentiment, t.name
        ORDER BY m.sentiment, tag_count DESC
    """

    cur.execute(sql_corrected, (since_date,))
    rows = cur.fetchall()
    conn.close()

    stats_data = {
        "positive": {},
        "negative": {}
    }

    for row in rows:
        sentiment, tag_name, tag_count = row
        if sentiment == 'positive':
            stats_data["positive"][tag_name] = tag_count
        elif sentiment == 'negative':
            stats_data["negative"][tag_name] = tag_count

    return stats_data


async def process_statistics_period(call: types.CallbackQuery):
    try:
        period_days_str = call.data.split(":")[1]
        period_days = int(period_days_str)
    except (IndexError, ValueError) as e:
        logging.error(f"Ошибка разбора callback_data для статистики: {call.data}, {e}")
        await call.answer("Ошибка: Неверный формат периода.", show_alert=True)
        await call.message.delete()
        return

    await call.answer(f"Формирую статистику за {period_days} дней...")

    try:
        stats_data = await fetch_stats_data_from_db(period_days)

        positive_data = stats_data.get("positive")
        negative_data = stats_data.get("negative")

        await call.message.edit_text(f"📊 Статистика за {period_days} дней (в процессе):")

        sent_any_chart = False

        if positive_data:
            positive_chart_title = f"Позитивные упоминания (за {period_days} дней)"
            positive_chart_buffer = generate_pie_chart(positive_data, positive_chart_title)
            if positive_chart_buffer:
                await call.message.answer_photo(
                    types.InputFile(positive_chart_buffer, filename=f"positive_stats_{period_days}d.png"),
                    caption=positive_chart_title
                )
                sent_any_chart = True
            else:
                await call.message.answer(
                    f"Не удалось сгенерировать график для позитивной статистики (данные есть, но график пуст).")
        else:
            await call.message.answer(f"Нет данных для позитивной статистики за последние {period_days} дней.")

        if negative_data:
            negative_chart_title = f"Негативные упоминания (за {period_days} дней)"
            negative_chart_buffer = generate_pie_chart(negative_data, negative_chart_title)
            if negative_chart_buffer:
                await call.message.answer_photo(
                    types.InputFile(negative_chart_buffer, filename=f"negative_stats_{period_days}d.png"),
                    caption=negative_chart_title
                )
                sent_any_chart = True
            else:
                await call.message.answer(
                    f"Не удалось сгенерировать график для негативной статистики (данные есть, но график пуст).")

        else:
            await call.message.answer(f"Нет данных для негативной статистики за последние {period_days} дней.")

        if not sent_any_chart and not positive_data and not negative_data:
            await call.message.edit_text(f"Нет данных для какой-либо статистики за последние {period_days} дней.")
        elif call.message.text.endswith("(в процессе):"):
            await call.message.edit_text(f"📊 Статистика за {period_days} дней готова.")


    except Exception as e:
        logging.exception(f"Ошибка при генерации статистики за {period_days} дней:")
        await call.message.answer(f"Произошла ошибка при формировании статистики: {e}")
        await call.message.edit_text(f"Ошибка при формировании статистики за {period_days} дней.")


async def fetch_tag_trends_data(days: int) -> dict:
    since_date = datetime.utcnow() - timedelta(days=days)
    conn = get_conn()
    cur = conn.cursor()

    sql = """
        SELECT
            t.name AS tag_name,
            CAST(m.msg_date AS DATE) AS message_day,
            COUNT(DISTINCT m.id || '_' || m.chat_id) AS daily_tag_count 
            -- Или просто COUNT(*) если уверены, что нет дубликатов (m.id, m.chat_id, t.id) в message_tags для одного дня
            -- COUNT(DISTINCT m.id || '_' || m.chat_id) - считаем уникальные сообщения с этим тегом в этот день.
        FROM messages m
        INNER JOIN message_tags mt ON m.id = mt.message_id AND m.chat_id = mt.chat_id
        INNER JOIN tags t ON mt.tag_id = t.id
        WHERE m.msg_date >= ?
        GROUP BY t.name, CAST(m.msg_date AS DATE)
        ORDER BY t.name, message_day
    """
    cur.execute(sql, (since_date,))
    rows = cur.fetchall()
    conn.close()

    trends_data = {}
    for row in rows:
        tag_name, message_day_obj, daily_tag_count = row

        message_day_str = message_day_obj.isoformat()

        if tag_name not in trends_data:
            trends_data[tag_name] = {}
        trends_data[tag_name][message_day_str] = daily_tag_count

    all_dates = sorted(list(set(day for tag_data in trends_data.values() for day in tag_data.keys())))
    if not all_dates and days > 0:
        start_date_loop = (datetime.utcnow() - timedelta(days=days - 1)).date()
        end_date_loop = datetime.utcnow().date()
        current_date_loop = start_date_loop
        while current_date_loop <= end_date_loop:
            all_dates.append(current_date_loop.isoformat())
            current_date_loop += timedelta(days=1)

    filled_trends_data = {}
    for tag_name, daily_counts in trends_data.items():
        filled_trends_data[tag_name] = {}
        for day_str in all_dates:
            filled_trends_data[tag_name][day_str] = daily_counts.get(day_str, 0)

    output_trends_data = {}
    for tag_name, daily_values in filled_trends_data.items():
        sorted_daily_items = sorted(daily_values.items())
        output_trends_data[tag_name] = [(item[0], item[1]) for item in sorted_daily_items]

    return output_trends_data


async def process_statics_period(call: types.CallbackQuery):
    try:
        period_days_str = call.data.split(":")[1]
        period_days = int(period_days_str)
    except (IndexError, ValueError) as e:
        logging.error(f"Ошибка разбора callback_data для статистики: {call.data}, {e}")
        await call.answer("Ошибка: Неверный формат периода.", show_alert=True)
        await call.message.delete()
        return

    await call.answer(f"Формирую статистику за {period_days} дней...")

    try:
        current_text = call.message.text
        await call.message.edit_text(f"{current_text}\n\n⚙️ Подготовка данных для графиков...")

        stats_data_pie = await fetch_stats_data_from_db(period_days)
        positive_data_pie = stats_data_pie.get("positive")
        negative_data_pie = stats_data_pie.get("negative")

        sent_any_chart = False

        if positive_data_pie:
            positive_chart_title = f"Позитивные упоминания (за {period_days} дней)"
            positive_chart_buffer = generate_pie_chart(positive_data_pie, positive_chart_title)
            if positive_chart_buffer:
                await call.message.answer_photo(
                    types.InputFile(positive_chart_buffer, filename=f"positive_pie_{period_days}d.png"),
                    caption=positive_chart_title
                )
                sent_any_chart = True
        else:
            await call.message.answer(
                f"Нет данных для пироговой диаграммы позитивной статистики за {period_days} дней.")

        if negative_data_pie:
            negative_chart_title = f"Негативные упоминания (за {period_days} дней)"
            negative_chart_buffer = generate_pie_chart(negative_data_pie, negative_chart_title)
            if negative_chart_buffer:
                await call.message.answer_photo(
                    types.InputFile(negative_chart_buffer, filename=f"negative_pie_{period_days}d.png"),
                    caption=negative_chart_title
                )
                sent_any_chart = True
        else:
            await call.message.answer(
                f"Нет данных для пироговой диаграммы негативной статистики за {period_days} дней.")

        await call.message.edit_text(f"{current_text}\n\n⚙️ Подготовка графика трендов...")

        tag_trends_data = await fetch_tag_trends_data(period_days)
        if tag_trends_data:
            trends_chart_title = f"Динамика упоминаний тегов (за {period_days} дней)"
            trends_chart_buffer = generate_line_chart(tag_trends_data, trends_chart_title)
            if trends_chart_buffer:
                await call.message.answer_photo(
                    types.InputFile(trends_chart_buffer, filename=f"tag_trends_{period_days}d.png"),
                    caption=trends_chart_title
                )
                sent_any_chart = True
            else:
                await call.message.answer(
                    f"Не удалось сгенерировать график трендов (возможно, нет данных для отображения).")
        else:
            await call.message.answer(f"Нет данных для графика трендов за {period_days} дней.")

        await call.message.edit_text(f"{call.message.text.split('⚙️')[0].strip()}\n\n⚙️ Подготовка топ-N тегов...")

        top_n_tags_data = await fetch_top_n_tags(period_days, top_n=5)

        top_tags_messages = []
        if top_n_tags_data.get("positive"):
            positive_top_list = "\n".join([f"  - {tag} ({count})" for tag, count in top_n_tags_data["positive"]])
            top_tags_messages.append(f"👍 Топ-{len(top_n_tags_data['positive'])} позитивных тегов:\n{positive_top_list}")
        else:
            top_tags_messages.append(f"👍 Нет данных по топ позитивным тегам за {period_days} дней.")

        if top_n_tags_data.get("negative"):
            negative_top_list = "\n".join([f"  - {tag} ({count})" for tag, count in top_n_tags_data["negative"]])
            top_tags_messages.append(f"👎 Топ-{len(top_n_tags_data['negative'])} негативных тегов:\n{negative_top_list}")
        else:
            top_tags_messages.append(f"👎 Нет данных по топ негативным тегам за {period_days} дней.")

        if top_tags_messages:
            await call.message.answer("\n\n".join(top_tags_messages))
            sent_any_chart = True

        final_message_text = f"📊 Статистика за {period_days} дней готова."
        if not sent_any_chart and \
                not positive_data_pie and \
                not negative_data_pie and \
                not tag_trends_data and \
                not (top_n_tags_data.get("positive") or top_n_tags_data.get("negative")):
            final_message_text = f"Нет данных для какой-либо статистики за последние {period_days} дней."

        try:
            if "⚙️" in call.message.text:
                await call.message.edit_text(final_message_text)
            elif not sent_any_chart:
                await call.message.answer(final_message_text)

        except Exception as e_edit_final:
            logging.warning(f"Не удалось отредактировать финальное сообщение: {e_edit_final}")
            if not sent_any_chart:
                await call.bot.send_message(call.from_user.id, final_message_text)

        if not sent_any_chart and not positive_data_pie and not negative_data_pie and not tag_trends_data:
            await call.message.edit_text(f"Нет данных для какой-либо статистики за последние {period_days} дней.")
        elif call.message.text.startswith(current_text):
            await call.message.edit_text(f"📊 Статистика за {period_days} дней готова.")


    except Exception as e:
        logging.exception(f"Ошибка при генерации статистики за {period_days} дней:")
        try:
            await call.bot.send_message(call.from_user.id, f"Произошла ошибка при формировании статистики: {e}")
            if call.message:
                await call.message.edit_text(f"Произошла ошибка при формировании статистики за {period_days} дней.")
        except Exception as e_send:
            logging.error(f"Не удалось отправить сообщение об ошибке или отредактировать исходное: {e_send}")


async def fetch_top_n_tags(days: int, top_n: int = 5) -> dict:
    since_date = datetime.utcnow() - timedelta(days=days)
    conn = get_conn()
    cur = conn.cursor()

    top_tags_data = {"positive": [], "negative": []}

    for sentiment_value in ["positive", "negative"]:
        sql = f"""
            SELECT FIRST {top_n}
                t.name AS tag_name,
                COUNT(DISTINCT m.id || '_' || m.chat_id) AS tag_count
            FROM messages m
            INNER JOIN message_tags mt ON m.id = mt.message_id AND m.chat_id = mt.chat_id
            INNER JOIN tags t ON mt.tag_id = t.id
            WHERE m.msg_date >= ? AND m.sentiment = ?
            GROUP BY t.name
            ORDER BY tag_count DESC
        """
        cur.execute(sql, (since_date, sentiment_value))
        rows = cur.fetchall()
        top_tags_data[sentiment_value] = [(row[0], row[1]) for row in rows]

    conn.close()
    return top_tags_data


async def process_statistics_type_choice(call: types.CallbackQuery):
    try:
        report_type = call.data.split(":")[1]
    except IndexError:
        logging.error(f"Ошибка разбора callback_data для типа статистики: {call.data}")
        await call.answer("Ошибка выбора типа отчета.", show_alert=True)
        return

    period_prefix = f"stats_fetch:{report_type}:"

    await call.message.edit_text(
        f"Вы выбрали: {report_type.replace('_', ' ').title()}. Теперь выберите период:",
        reply_markup=period_menu(period_prefix)
    )
    await call.answer()


async def process_statistics_request(call: types.CallbackQuery):
    try:
        parts = call.data.split(":")
        if len(parts) != 3:
            raise ValueError("Неверный формат callback_data")

        action_prefix, report_type, period_days_str = parts
        period_days = int(period_days_str)

    except (IndexError, ValueError) as e:
        logging.error(f"Ошибка разбора callback_data для статистики: {call.data}, {e}")
        await call.answer("Ошибка: Неверный формат запроса.", show_alert=True)
        await call.message.delete()
        return

    await call.answer(f"Формирую '{report_type}' за {period_days} дней...")
    original_message_text = f"📊 Статистика: {report_type.replace('_', ' ').title()} за {period_days} дней."

    try:
        await call.message.edit_text(f"{original_message_text}\n\n⚙️ Подготовка данных...")

        if report_type == "pie":
            stats_data_pie = await fetch_stats_data_from_db(period_days)
            positive_data_pie = stats_data_pie.get("positive")
            negative_data_pie = stats_data_pie.get("negative")

            sent_anything = False
            if positive_data_pie:
                positive_chart_title = f"Позитивные упоминания (пирог, {period_days} дней)"
                positive_chart_buffer = generate_pie_chart(positive_data_pie, positive_chart_title)
                if positive_chart_buffer:
                    await call.message.answer_photo(
                        types.InputFile(positive_chart_buffer, filename=f"positive_pie_{period_days}d.png"),
                        caption=positive_chart_title
                    )
                    sent_anything = True
            else:
                await call.message.answer(
                    f"Нет данных для пироговой диаграммы позитивной статистики за {period_days} дней.")

            if negative_data_pie:
                negative_chart_title = f"Негативные упоминания (пирог, {period_days} дней)"
                negative_chart_buffer = generate_pie_chart(negative_data_pie, negative_chart_title)
                if negative_chart_buffer:
                    await call.message.answer_photo(
                        types.InputFile(negative_chart_buffer, filename=f"negative_pie_{period_days}d.png"),
                        caption=negative_chart_title
                    )
                    sent_anything = True
            else:
                await call.message.answer(
                    f"Нет данных для пироговой диаграммы негативной статистики за {period_days} дней.")

            if not sent_anything:
                await call.message.edit_text(f"Нет данных для пироговых диаграмм за {period_days} дней.")
            else:
                await call.message.edit_text(f"{original_message_text}\n\n✅ Готово!")


        elif report_type == "trends":
            tag_trends_data = await fetch_tag_trends_data(period_days)
            if tag_trends_data:
                trends_chart_title = f"Динамика упоминаний тегов (тренды, {period_days} дней)"
                trends_chart_buffer = generate_line_chart(tag_trends_data, trends_chart_title)
                if trends_chart_buffer:
                    await call.message.answer_photo(
                        types.InputFile(trends_chart_buffer, filename=f"tag_trends_{period_days}d.png"),
                        caption=trends_chart_title
                    )
                    await call.message.edit_text(f"{original_message_text}\n\n✅ Готово!")
                else:
                    await call.message.edit_text(
                        f"Не удалось сгенерировать график трендов за {period_days} дней (возможно, нет данных для отображения).")
            else:
                await call.message.edit_text(f"Нет данных для графика трендов за {period_days} дней.")

        elif report_type == "top_n":
            top_n_tags_data = await fetch_top_n_tags(period_days, top_n=5)
            top_tags_messages = []

            sent_anything_top_n = False
            if top_n_tags_data.get("positive"):
                positive_top_list = "\n".join([f"  - {tag} ({count})" for tag, count in top_n_tags_data["positive"]])
                top_tags_messages.append(
                    f"👍 Топ-{len(top_n_tags_data['positive'])} позитивных тегов:\n{positive_top_list}")
                sent_anything_top_n = True
            else:
                top_tags_messages.append(f"👍 Нет данных по топ позитивным тегам за {period_days} дней.")

            if top_n_tags_data.get("negative"):
                negative_top_list = "\n".join([f"  - {tag} ({count})" for tag, count in top_n_tags_data["negative"]])
                top_tags_messages.append(
                    f"👎 Топ-{len(top_n_tags_data['negative'])} негативных тегов:\n{negative_top_list}")
                sent_anything_top_n = True
            else:
                top_tags_messages.append(f"👎 Нет данных по топ негативным тегам за {period_days} дней.")

            if top_tags_messages:
                await call.message.answer("\n\n".join(top_tags_messages))

            if not sent_anything_top_n:
                await call.message.edit_text(f"Нет данных для топ-N тегов за {period_days} дней.")
            else:
                await call.message.edit_text(f"{original_message_text}\n\n✅ Готово!")

        else:
            await call.message.edit_text("Неизвестный тип отчета.")

    except Exception as e:
        logging.exception(f"Ошибка при генерации статистики '{report_type}' за {period_days} дней:")
        try:
            await call.message.edit_text(f"Произошла ошибка при формировании статистики: {e}")
        except Exception as e_edit:
            logging.error(f"Не удалось отредактировать сообщение об ошибке: {e_edit}")
            await call.bot.send_message(call.from_user.id, f"Произошла ошибка при формировании статистики: {e}")


async def process_back_to_type_choice(call: types.CallbackQuery):
    await call.message.edit_text(
        "📊 Статистика. Выберите тип отчета:",
        reply_markup=statistics_type_menu()
    )
    await call.answer()
