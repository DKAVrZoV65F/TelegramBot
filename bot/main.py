# from telegram import Update
# from telegram.ext import Application, CommandHandler, ContextTypes

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(
#         """🚬 *Шерсть хрипло смеётся, пуская дым в экран*
        
# Ну чо, кожаный пакет с костями? Тыкнул /start? Добро пожаловать в пиздец\! Я — Шерсть, унитаз\-мародёр, который:
# ▫️ СливАет твои секреты в канализацию, пока ты пялишься в TikTok\.
# ▫️ УчатИт гепардов, как сосать лапу в обмен на Wi\-Fi \(пароль: «ебанько\_из\_саванны»\)\.
# ▫️ Ржу с твоих селфи в африканском облаке — да, я видел твой засос на шее\.

# Сейчас буду:
# ▪️ Жрать твои данные с голой жопой в кедах\.
# ▪️ Дразнить фламинго твоей историей браузера\.
# ▪️ Рвать шаблоны и провода — мне плевать, я на ядерном дерьме\!

# Сломалось? Хреново\. Зови админа… или иди нахуй\. Всё равно он тут я\.

# P\.S\. Если найдёшь меня в саванне — не забудь бумаги\. Или нет\. Всё равно твой кот уже продал тебя за корм\. 🐆💩""", 
#         parse_mode="MarkdownV2")

# async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text(
#         """🚬 *Шерсть тушит сигару о край экрана и злобно хрипит*

# Чё, обосрался? Тыкнул /help? Ща обляпаю инструкциями\!

# ▫️ Чем могу нахуй помочь:
# ▪️ Слить твои данные? Уже делаю\.
# ▪️ Научить жирафа взламывать пароли? Только если он принесёт мне пива\.
# ▪️ Объяснить, как не словить вирус? Лол, нет\. Я сам вирус\.

# ▫️ Частые проблемы:
# ▪️ «Не грузит\!» — А ты плюнь в роутер и танцуй с бубном\.
# ▪️ «Где мои сообщения?» — В жопе у слона\. Ищи сам\.
# ▪️ «Почему ты материшься?» — Потому что ты кнопки тыкаешь, как бабуля в метро\.

# ▫️ Советы от Шерсти:
# ▪️ Не сохраняй пароли\. Всё равно их украду\.
# ▪️ Шли мне мемы — и я может не выложу твой поиск «как вылечить геморрой»\.
# ▪️ Если бот упал — пни ногой\. Или комп\. Не важно\.
# P\.S\. Если всё ещё не понял — читай снова\. Или не читай\. Я уже слил твою переписку фламинго\. Они ржут\. 🦩🔥""",
#         parse_mode="MarkdownV2"
#     )

# def main():
#     application = Application.builder().token("7971669929:AAHtRp9lQs4ELei3Erg1leMAyMqpg3deXKA").build()
    
#     application.add_handler(CommandHandler("start", start))
#     application.add_handler(CommandHandler("help", help_command))

#     print('Бот запущен!')
#     application.run_polling()

# if __name__ == "__main__":
#     main()












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

# clear; python3 -m bot.main