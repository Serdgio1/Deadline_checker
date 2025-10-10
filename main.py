import asyncio
import logging
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
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

class DeadlineForm(StatesGroup):
    waiting_for_deadline = State()

class NotificationForm(StatesGroup):
    waiting_for_notification = State()

class AllNotify(StatesGroup):
    all_notify = State()

async def check_deadlines():
    records = get_all_records()
    today = datetime.today().date()
    cursor.execute("SELECT chat_id FROM users")
    chat_ids = [row[0] for row in cursor.fetchall() if row[0]]
    
    for i, record in enumerate(records, start=2):
        try:
            deadline_date = datetime.strptime(record["Deadline"], "%d.%m.%Y").date()
            name = record.get("Name", "No description")
            
            if deadline_date - today == timedelta(days=7):
                for chat_id in chat_ids:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"<b>Weekly Reminder</b>\n\n1 week left until <b>{deadline_date}</b>\n<b>{name}</b>\n\n<i>Time to start planning!</i>"
                    )

            if deadline_date - today == timedelta(days=1):
                for chat_id in chat_ids:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"<b>Final Reminder</b>\n\nTomorrow is the deadline: <b>{deadline_date}</b>\n<b>{name}</b>\n\n<i>Last chance to finish!</i>"
                    )

            elif deadline_date == today:
                for chat_id in chat_ids:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"<b>DEADLINE TODAY!</b>\n\n<b>{deadline_date}</b>\n<b>{name}</b>\n\n<i>Submit now!</i>"
                    )
            elif today - deadline_date == timedelta(days=1):
                for chat_id in chat_ids:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=f"<b>Deadline Expired</b>\n\nYesterday was the deadline: <b>{deadline_date}</b>\n<b>{name}</b>\n\n<i>This task will be deleted now.</i>"
                    )
                delete_row(i)
        except Exception as e:
            print("Error parsing record:", record, e)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    welcome_text = f"""
<b>Welcome to Deadline Checker Bot</b>

Hello, {html.bold(html.quote(message.from_user.full_name))}!

<b>Features:</b>
• Send daily reminders at 12:00 PM
• Show all your deadlines
• Enable/disable notifications
• View assignments to pass
• Auto-delete expired deadlines

<b>Quick Start:</b>
1. Click "Notifications" to enable reminders
2. Click "Deadlines" to see all tasks
3. Admins can use /add_deadline to add new deadlines

<b>Format for adding deadlines:</b>
<code>DD.MM.YYYY Subject Link</code>

<i>I'll remind you 7 days before, 1 day before, on the deadline day, and delete expired tasks automatically.</i>
"""
    await message.answer(welcome_text, reply_markup=get_keyboard([('Deadlines','deadlines'),('See my points','points'),('Notifications','notify'),('Pass','pass')]))

@dp.callback_query(F.data=='points')
async def points_handler(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("This feature is not available yet. Please wait for the next release.")
    await callback.answer()

@dp.callback_query(F.data=='deadlines')
async def deadlines_handler(callback: CallbackQuery):
    text = all_deadlines(get_all_records())
    if text.strip():
        response = f"<b>Your Deadlines:</b>\n\n{text}\n\n<i>Reminders sent daily at 12:00 PM</i>"
    else:
        response = "<b>Your Deadlines:</b>\n\n<i>No deadlines found! You're all caught up!</i>\n\n<i>Reminders sent daily at 12:00 PM</i>"
    await callback.message.delete()
    await callback.message.answer(response, disable_web_page_preview=True)
    await callback.answer()

@dp.callback_query(F.data=='notify')
async def notify_handler(callback: CallbackQuery, state: FSMContext):
    notification_text = """
<b>Notification Setup</b>

To enable notifications, please type 'Yes'

<b>What you'll receive:</b>
• Daily reminders at 12:00 PM
• 7 days before deadline
• 1 day before deadline  
• On deadline day
• Auto-deletion notice

<i>Type 'Yes' to continue or anything else to cancel.</i>
"""
    await callback.message.answer(notification_text)
    await state.set_state(NotificationForm.waiting_for_notification)
    await callback.answer()

@dp.callback_query(F.data=='pass')
async def pass_task(callback: CallbackQuery):
    text = all_deadlines(get_all_records(),['Name','Pass'])
    if text.strip():
        response = f"<b>Works to Pass:</b>\n\n{text}\n\n<i>Keep up the good work!</i>"
    else:
        response = "<b>Works to Pass:</b>\n\n<i>No pending works to pass! Great job!</i>"
    await callback.message.delete()
    await callback.message.answer(response)
    await callback.answer()

def is_admin(chat_id):
    cursor.execute("SELECT role FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    return row and row[0] == 'admin'

@dp.message(F.text=='/add_deadline')
async def add_deadline_handler(message: Message, state: FSMContext):
    if not is_admin(message.chat.id):
        error_text = """
<b>Access Denied</b>

You do not have permission to add deadlines.

<i>Only admins can use this command.</i>
"""
        await message.answer(error_text)
        return
    
    add_deadline_text = """
<b>Add New Deadline</b>

Please enter the deadline in the following format:

<code>DD.MM.YYYY Subject Link</code>

<b>Example:</b>
<code>25.12.2024 Christmas Assignment https://example.com</code>

<b>Required:</b>
• Date (DD.MM.YYYY)
• Subject/Description
• Link (optional but recommended)

<i>Type your deadline details now...</i>
"""
    await message.answer(add_deadline_text)
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
        error_text = """
<b>Invalid Format</b>

Please use the correct format:
<code>DD.MM.YYYY Subject Link</code>

<b>Example:</b>
<code>25.12.2024 Christmas Assignment https://example.com</code>

<b>Requirements:</b>
• Date in DD.MM.YYYY format
• At least 3 words (date + subject + link)
"""
        await message.answer(error_text)
        return
    
    add_row(deadline_add)
    success_text = f"""
<b>Deadline Added Successfully!</b>

<b>Added:</b> <code>{deadline_text}</code>

<i>The deadline has been recorded and users will receive reminders automatically!</i>
"""
    await message.answer(success_text)
    await state.clear()

@dp.message(NotificationForm.waiting_for_notification)
async def process_notification(message: Message, state: FSMContext):
    if message.text == 'Yes':
        role = 'admin' if message.from_user.username == 'Sergio_Suprun' else 'user'
        cursor.execute("INSERT OR IGNORE INTO users (chat_id, username, role) VALUES (?, ?, ?)", 
                       (message.chat.id, message.from_user.username, role))
        if role == 'admin':
            cursor.execute("UPDATE users SET role = 'admin' WHERE chat_id = ?", (message.chat.id,))
        con.commit()
        
        success_text = f"""
<b>Notifications Enabled Successfully!</b>

<b>You will now receive:</b>
• Daily reminders at 12:00 PM
• 7 days before deadline
• 1 day before deadline
• On deadline day
• Auto-deletion notices

<i>You're all set! I'll keep you updated on your deadlines.</i>
"""
        await message.answer(success_text)
    else:
        cancel_text = """
<b>Notifications Not Enabled</b>

You won't receive deadline reminders.

<i>You can enable them later by clicking the 'Notifications' button anytime!</i>
"""
        await message.answer(cancel_text)
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
    scheduler.add_job(check_deadlines, "cron", hour=12, minute=0)
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