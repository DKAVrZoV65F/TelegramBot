# handlers/common.py

from aiogram import types


async def cmd_start(m: types.Message):
    await m.answer("👋 Привет! Я собираю сообщения из групп.")


async def cmd_help(m: types.Message):
    await m.answer("/menu – админ-панель\n/help – помощь")


def register(dp):
    dp.register_message_handler(cmd_start, commands=["start"])
    dp.register_message_handler(cmd_help, commands=["help"])
