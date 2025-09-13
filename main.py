import asyncio
import logging
import sys
import sqlite3
import re

from aiogram import Bot, Dispatcher, Router, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN
from utilities import get_keyboard, all_deadlines
from sheets import get_all_records, add_row


dp = Dispatcher()
router = Router()
bot = Bot(token=BOT_TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))

class DeadlineForm(StatesGroup):
    waiting_for_deadline = State()

async def check_deadlines():
    records = get_all_records()
    today = datetime.today().date()
    for record in records:
        try:
            # Assuming date is stored in column "Deadline" as "DD.MM.YYYY"
            deadline_date = datetime.strptime(record["Deadline"], "%d.%m.%Y").date()
            name = record.get("Name", "No description")

            # Remind 7 days before
            if deadline_date - today == timedelta(days=7):
                await bot.send_message(
                    chat_id="", 
                    text=f"Reminder: 1 week left until {deadline_date} — {name}"
                )

            # Remind 1 day before
            if deadline_date - today == timedelta(days=1):
                await bot.send_message(
                    chat_id="", 
                    text=f"Reminder: Tomorrow is the deadline {deadline_date} — {name}"
                )

        except Exception as e:
            print("Error parsing record:", record, e)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(message.from_user.full_name)}!",reply_markup=get_keyboard())

@dp.callback_query(F.data=='deadlines')
async def deadlines_handler(callback: CallbackQuery):
    text = all_deadlines(get_all_records())
    await callback.message.delete()
    await callback.message.answer(f"Here are your deadlines:\n{text}")
    await callback.answer()

@dp.message(F.text=='/add_deadline')
async def add_deadline_handler(message: Message, state: FSMContext):
    await message.answer("Please enter the deadline: (DD.MM.YYYY) Subject Link")
    await state.set_state(DeadlineForm.waiting_for_deadline)

@dp.message(DeadlineForm.waiting_for_deadline)
async def process_deadline(message: Message, state: FSMContext):
    deadline_text = message.text.strip()
    deadline_add = list(map(str, deadline_text.split(' ')))
    if re.match(r'\d{2}.\d{2}.\d{4}', deadline_add[0]) is None or len(deadline_add) < 3:
        await message.answer("Invalid format. Please use: DD.MM.YYYY Subject Link")
        return
    add_row(deadline_add)
    await message.answer(f"Deadline '{deadline_text}' received and recorded.")
    await state.clear()

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_deadlines, "interval", seconds=10)  # check every day
    scheduler.start()
    await dp.start_polling(bot)

if __name__=='__main__':
    con = sqlite3.connect('bot_data.db')
    cursor = con.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        state TEXT
    )
''')
    con.commit()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
    main()

