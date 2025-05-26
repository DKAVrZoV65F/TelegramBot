# keyboards/statistics_keyboards.py

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def statistics_type_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton("📊 Общая (пироги)", callback_data="stats_type:pie"),
        InlineKeyboardButton("📈 Динамика тегов (тренды)", callback_data="stats_type:trends"),
        InlineKeyboardButton("🏆 Топ-N тегов", callback_data="stats_type:top_n"),
        InlineKeyboardButton("❌ Закрыть", callback_data="close_notify")
    )


def period_menu(prefix_with_type: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton("7 дней", callback_data=f"{prefix_with_type}7"),
            InlineKeyboardButton("30 дней", callback_data=f"{prefix_with_type}30"),
        ],
        [InlineKeyboardButton("⬅️ Назад к выбору отчета", callback_data="stats_back_to_type")],
        [InlineKeyboardButton("❌ Закрыть меню", callback_data="close_notify")]
    ])
