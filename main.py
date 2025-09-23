import asyncio
import logging
from pydoc import text
import sys
import sqlite3
import re
import os

from aiogram import Bot, Dispatcher, Router, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from utilities import get_keyboard, all_deadlines
from sheets import get_all_records, add_row, delete_row

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

dp = Dispatcher()
router = Router()
bot = Bot(token=BOT_TOKEN,default=DefaultBotProperties(parse_mode=ParseMode.HTML))

class DeadlineForm(StatesGroup):
    waiting_for_deadline = State()

class NotificationForm(StatesGroup):
    waiting_for_notification = State()

class AllNotify(StatesGroup):
    all_notify = State()

async def check_deadlines():
    records = get_all_records()
    today = datetime.today().date()
    now = datetime.now()
    cursor.execute("SELECT chat_id FROM users")
    chat_ids = [row[0] for row in cursor.fetchall() if row[0]]
    for i, record in enumerate(records, start=2):
        try:
            # Assuming date is stored in column "Deadline" as "DD.MM.YYYY"
            deadline_date = datetime.strptime(record["Deadline"], "%d.%m.%Y").date()
            name = record.get("Name", "No description")
            if now.time().hour == 12 and now.time().minute >= 0:
                # Remind 7 days before
                if deadline_date - today == timedelta(days=7):
                    for chat_id in chat_ids:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"Reminder: 1 week left until {deadline_date} — {name}"
                        )

                # Remind 1 day before
                if deadline_date - today == timedelta(days=1):
                    for chat_id in chat_ids:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"Reminder: Tomorrow is the deadline {deadline_date} — {name}"
                        )

                elif deadline_date == today:
                    for chat_id in chat_ids:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"Deadline today: {deadline_date} — {name}"
                        )
                    delete_row(i)
                elif today - deadline_date == timedelta(days=1):
                    for chat_id in chat_ids:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=f"Reminder: Yesterday was the deadline {deadline_date.date()} — {name}\n It will delete now"
                        )
                    delete_row(i)
        except Exception as e:
            print("Error parsing record:", record, e)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(f"Hello, {html.bold(html.quote(message.from_user.full_name))}!",reply_markup=get_keyboard([('Deadlines','deadlines'),('See my points','points'),('Notifications','notify'),('Pass','pass')]))

@dp.callback_query(F.data=='points')
async def points_handler(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("That doesn't work. Wait for a new release.")
    await callback.answer()

@dp.callback_query(F.data=='deadlines')
async def deadlines_handler(callback: CallbackQuery):
    text = all_deadlines(get_all_records())
    await callback.message.delete()
    await callback.message.answer(f"Here are your deadlines:\n{text}", disable_web_page_preview=True)
    await callback.answer()

@dp.callback_query(F.data=='notify')
async def notify_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("To enable notifications, please type 'Yes'.")
    await state.set_state(NotificationForm.waiting_for_notification)
    await callback.answer()

@dp.callback_query(F.data=='pass')
async def pass_task(callback: CallbackQuery):
    text = all_deadlines(get_all_records(),['Name','Pass'])
    await callback.message.delete()
    await callback.message.answer(f"Here are your works to pass:\n{text}")
    await callback.answer()



# Helper function to check if user is admin
def is_admin(chat_id):
    cursor.execute("SELECT role FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    return row and row[0] == 'admin'

@dp.message(F.text=='/add_deadline')
async def add_deadline_handler(message: Message, state: FSMContext):
    if not is_admin(message.chat.id):
        await message.answer("You do not have permission to add deadlines. Only admins can use this command.")
        return
    await message.answer("Please enter the deadline: (DD.MM.YYYY) Subject Link")
    await state.set_state(DeadlineForm.waiting_for_deadline)

@dp.message(F.text=='/all')
async def message_to_all(message: Message, state: FSMContext):
    if is_admin(message.chat.id):
        await message.answer(text="Type a message to all users")
        await state.set_state(AllNotify.all_notify)

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

@dp.message(NotificationForm.waiting_for_notification)
async def process_notification(message: Message, state: FSMContext):
    if message.text == 'Yes':
        role = 'admin' if message.from_user.username == 'Sergio_Suprun' else 'user'
        cursor.execute("INSERT OR IGNORE INTO users (chat_id, username, role) VALUES (?, ?, ?)", 
                       (message.chat.id, message.from_user.username, role))
        # If user already exists, update role if needed
        if role == 'admin':
            cursor.execute("UPDATE users SET role = 'admin' WHERE chat_id = ?", (message.chat.id,))
        con.commit()
        await message.answer("Notifications enabled. You will receive reminders about upcoming deadlines.")
    else:
        await message.answer("Notifications not enabled. You can enable them later by clicking the 'Notifications' button.")
    await state.clear()

@dp.message(AllNotify.all_notify)
async def process_all_notify(message: Message, state: FSMContext):
    if is_admin(message.chat.id):
        text = message.text.strip()
        cursor.execute("SELECT chat_id FROM users")
        chat_ids = [row[0] for row in cursor.fetchall() if row[0]]
        for chat_id in chat_ids:
            await bot.send_message(chat_id=chat_id, text=text)
        await message.answer("Message sent to all users.")
    else:
        await message.answer("You do not have permission to send messages to all users.")
    await state.clear()

async def main():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_deadlines, "interval", hours = 1)  # check every day
    scheduler.start()
    await dp.start_polling(bot)

if __name__=='__main__':
    con = sqlite3.connect('bot_data.db')
    cursor = con.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER UNIQUE,
        username TEXT,
        role TEXT
    )
''')
    con.commit()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
    main()

