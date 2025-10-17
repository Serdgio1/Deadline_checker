from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

async def start():
    dp = Dispatcher()
    bot = Bot(token=BOT_TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)