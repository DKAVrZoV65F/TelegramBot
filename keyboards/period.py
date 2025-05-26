# keyboards/period.py

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def period_menu(prefix: str) -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(inline_keyboard=[
    [
      InlineKeyboardButton("Сегодня", callback_data=f"{prefix}day"),
      InlineKeyboardButton("7 дней",  callback_data=f"{prefix}week"),
      InlineKeyboardButton("30 дней", callback_data=f"{prefix}month"),
    ],
    [InlineKeyboardButton("❌ Закрыть", callback_data="close_notify")]
  ])
