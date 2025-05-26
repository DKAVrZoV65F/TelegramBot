# keyboards/admin.py

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(row_width=2).add(
        InlineKeyboardButton("📝 Необработанные", callback_data="req:uproc"),
        InlineKeyboardButton("📄 XML-экспорт", callback_data="req:uproc_xml"),
        InlineKeyboardButton("📋 XLSX-экспорт", callback_data="export_xlsx"),
    )
