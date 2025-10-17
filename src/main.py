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
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, BotCommand
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from utilities import get_keyboard, all_deadlines
from sheets import get_all_records, add_row, delete_row
from config import DATABASE_PATH, ADMIN_USERNAMES

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

class QueueForm(StatesGroup):
    waiting_for_queue_name = State()
    waiting_for_priority_user = State()
    waiting_for_queue_action = State()

async def check_deadlines():
    records = get_all_records()
    today = datetime.today().date()
    cursor.execute("SELECT chat_id FROM users")
    chat_ids = [row[0] for row in cursor.fetchall() if row[0]]
    rows_to_delete = []
    
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
                rows_to_delete.append(i)
        except Exception as e:
            print("Error parsing record:", record, e)
    
    for row_number in reversed(rows_to_delete):
        delete_row(row_number)


# Queue Management Functions
def create_queue(queue_name):
    """Create a new queue"""
    cursor.execute("INSERT OR IGNORE INTO queues (name) VALUES (?)", (queue_name,))
    con.commit()
    return cursor.lastrowid

def join_queue(queue_name, chat_id, username):
    """Join a queue"""
    cursor.execute("SELECT id FROM queues WHERE name = ?", (queue_name,))
    queue = cursor.fetchone()
    if not queue:
        return False, "Queue not found"
    
    queue_id = queue[0]
    cursor.execute("SELECT id FROM queue_members WHERE queue_id = ? AND chat_id = ?", (queue_id, chat_id))
    if cursor.fetchone():
        return False, "You are already in this queue"
    
    cursor.execute("INSERT INTO queue_members (queue_id, chat_id, username, priority, joined_at) VALUES (?, ?, ?, 0, datetime('now'))", 
                   (queue_id, chat_id, username))
    con.commit()
    return True, "Successfully joined the queue"

def leave_queue(queue_name, chat_id):
    """Leave a queue"""
    cursor.execute("SELECT id FROM queues WHERE name = ?", (queue_name,))
    queue = cursor.fetchone()
    if not queue:
        return False, "Queue not found"
    
    queue_id = queue[0]
    cursor.execute("DELETE FROM queue_members WHERE queue_id = ? AND chat_id = ?", (queue_id, chat_id))
    con.commit()
    return True, "Successfully left the queue"

def get_queue_members(queue_name):
    """Get all members of a queue ordered by priority and join time"""
    cursor.execute("""
        SELECT qm.chat_id, qm.username, qm.priority, qm.joined_at 
        FROM queue_members qm 
        JOIN queues q ON qm.queue_id = q.id 
        WHERE q.name = ? 
        ORDER BY qm.priority DESC, qm.joined_at ASC
    """, (queue_name,))
    return cursor.fetchall()

def get_all_queues():
    """Get all available queues"""
    cursor.execute("SELECT name FROM queues")
    return [row[0] for row in cursor.fetchall()]

def delete_queue(queue_name):
    """Delete a queue and all its members"""
    cursor.execute("SELECT id FROM queues WHERE name = ?", (queue_name,))
    queue = cursor.fetchone()
    if not queue:
        return False, "Queue not found"
    
    queue_id = queue[0]
    cursor.execute("DELETE FROM queue_members WHERE queue_id = ?", (queue_id,))
    cursor.execute("DELETE FROM queues WHERE id = ?", (queue_id,))
    con.commit()
    return True, "Queue deleted successfully"

def set_priority(queue_name, username, priority):
    """Set priority for a user in a queue"""
    cursor.execute("SELECT id FROM queues WHERE name = ?", (queue_name,))
    queue = cursor.fetchone()
    if not queue:
        return False, "Queue not found"
    
    queue_id = queue[0]
    cursor.execute("UPDATE queue_members SET priority = ? WHERE queue_id = ? AND username = ?", 
                   (priority, queue_id, username))
    if cursor.rowcount == 0:
        return False, "User not found in queue"
    
    con.commit()
    return True, f"Priority set to {priority} for {username}"

def shuffle_queue(queue_name):
    """Randomly shuffle queue members"""
    cursor.execute("SELECT id FROM queues WHERE name = ?", (queue_name,))
    queue = cursor.fetchone()
    if not queue:
        return False, "Queue not found"
    
    queue_id = queue[0]
    cursor.execute("SELECT id FROM queue_members WHERE queue_id = ?", (queue_id,))
    members = cursor.fetchall()
    
    if len(members) < 2:
        return False, "Need at least 2 members to shuffle"
    
    # Get all member IDs and shuffle them
    import random
    member_ids = [member[0] for member in members]
    random.shuffle(member_ids)
    
    # Update join times to reflect new order (most recent first for shuffled order)
    current_time = datetime.now()
    for i, member_id in enumerate(member_ids):
        new_time = current_time - timedelta(seconds=i)
        cursor.execute("UPDATE queue_members SET joined_at = ? WHERE id = ?", 
                       (new_time.strftime('%Y-%m-%d %H:%M:%S'), member_id))
    
    con.commit()
    return True, f"Queue '{queue_name}' has been shuffled randomly"

async def setup_bot_commands():
    """Set up bot commands menu"""
    commands = [
        BotCommand(command="start", description="🚀 Start the bot"),
        BotCommand(command="queues", description="📋 Show all queues"),
        BotCommand(command="deadlines", description="📅 View deadlines"),
        BotCommand(command="notify", description="🔔 Enable notifications"),
        BotCommand(command="pass", description="📝 View works to pass"),
    ]
    await bot.set_my_commands(commands)

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    welcome_text = f"""
<b>Welcome to Deadline Checker Bot</b>

Hello, {html.bold(html.quote(message.from_user.full_name))}!

<b>Features:</b>
• Send daily reminders at 12:00 PM
• Show all your deadlines
• Enable notifications
• View assignments to pass
• Auto-delete expired deadlines
• Queue system for subjects

<b>Quick Start:</b>
1. Use the menu button to access commands
2. Click "Notifications" to enable reminders
3. Click "Deadlines" to see all tasks
4. Click "Queues" to see available queues

<b>Available Commands:</b>
• <code>/join [name]</code> - Join a queue
• <code>/leave [name]</code> - Leave a queue
• <code>/show [name]</code> - Show queue members
• <code>/queues</code> - Show all queues
• <code>/deadlines</code> - View deadlines
• <code>/notify</code> - Enable notifications
• <code>/pass</code> - View works to pass

<i>I'll remind you 7 days before, 1 day before, on the deadline day, and delete expired tasks automatically.</i>
"""
    await message.answer(welcome_text, reply_markup=get_keyboard([('Deadlines','deadlines'),('See my points','points'),('Notifications','notify'),('Pass','pass'),('Queues','queues')]))

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

@dp.callback_query(F.data=='queues')
async def queues_handler(callback: CallbackQuery):
    queues = get_all_queues()
    if queues:
        queue_list = "\n".join([f"• {queue}" for queue in queues])
        response = f"<b>Available Queues:</b>\n\n{queue_list}\n\n<i>Use /queues to see all queues</i>"
    else:
        response = "<b>Available Queues:</b>\n\n<i>No queues available yet. Admins can create queues using /create_queue [name]</i>"
    
    await callback.message.delete()
    await callback.message.answer(response)
    await callback.answer()

def is_admin(chat_id, username=None):
    # Check if user is in admin usernames list from environment
    if username and username in ADMIN_USERNAMES:
        return True
    
    # Check database role
    cursor.execute("SELECT role FROM users WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    return row and row[0] == 'admin'

@dp.message(F.text=='/add_deadline')
async def add_deadline_handler(message: Message, state: FSMContext):
    if not is_admin(message.chat.id, message.from_user.username):
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
    if is_admin(message.chat.id, message.from_user.username):
        await message.answer(text="Type a message to all users")
        await state.set_state(AllNotify.all_notify)

# Queue Management Commands
@dp.message(F.text.startswith('/create_queue'))
async def create_queue_handler(message: Message):
    if not is_admin(message.chat.id, message.from_user.username):
        await message.answer("<b>Access Denied</b>\n\nOnly admins can create queues.")
        return
    
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.answer("<b>Usage:</b> <code>/create_queue [queue_name]</code>\n\n<b>Example:</b> <code>/create_queue Math</code>")
        return
    
    queue_name = parts[1].strip()
    create_queue(queue_name)
    
    # Send notification to all users about the new queue
    cursor.execute("SELECT chat_id FROM users")
    chat_ids = [row[0] for row in cursor.fetchall() if row[0]]
    
    notification_text = f"""
<b>📋 New Queue Created!</b>

A new queue '<b>{queue_name}</b>' has been created by an admin.

<b>How to join:</b>
• Use command: <code>/join {queue_name}</code>
• Or use: <code>/join_queue {queue_name}</code>
• Or click the "Queues" button in the menu

<i>Join now to be part of the queue!</i>
"""
    
    # Send notification to all users
    for chat_id in chat_ids:
        try:
            await bot.send_message(chat_id=chat_id, text=notification_text)
        except Exception as e:
            print(f"Failed to send notification to chat_id {chat_id}: {e}")
    
    await message.answer(f"<b>Queue Created!</b>\n\nQueue '<b>{queue_name}</b>' has been created successfully.\n\nAll users have been notified about the new queue.\n\nUsers can now join using: <code>/join_queue {queue_name}</code>")

@dp.message(F.text.startswith('/join_queue'))
async def join_queue_handler(message: Message):
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.answer("<b>Usage:</b> <code>/join_queue [queue_name]</code>\n\n<b>Example:</b> <code>/join_queue Math</code>")
        return
    
    queue_name = parts[1].strip()
    username = message.from_user.username or message.from_user.full_name
    success, msg = join_queue(queue_name, message.chat.id, username)
    
    if success:
        await message.answer(f"<b>Successfully Joined!</b>\n\nYou have joined the '<b>{queue_name}</b>' queue.\n\nUse <code>/show_queue {queue_name}</code> to see the current queue.")
    else:
        await message.answer(f"<b>Error:</b> {msg}")

@dp.message(F.text.startswith('/leave_queue'))
async def leave_queue_handler(message: Message):
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.answer("<b>Usage:</b> <code>/leave_queue [queue_name]</code>\n\n<b>Example:</b> <code>/leave_queue Math</code>")
        return
    
    queue_name = parts[1].strip()
    success, msg = leave_queue(queue_name, message.chat.id)
    
    if success:
        await message.answer(f"<b>Successfully Left!</b>\n\nYou have left the '<b>{queue_name}</b>' queue.")
    else:
        await message.answer(f"<b>Error:</b> {msg}")

@dp.message(F.text.startswith('/show_queue'))
async def show_queue_handler(message: Message):
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.answer("<b>Usage:</b> <code>/show_queue [queue_name]</code>\n\n<b>Example:</b> <code>/show_queue Math</code>")
        return
    
    queue_name = parts[1].strip()
    members = get_queue_members(queue_name)
    
    if not members:
        await message.answer(f"<b>Queue: {queue_name}</b>\n\n<i>No members in this queue yet.</i>")
        return
    
    queue_text = f"<b>Queue: {queue_name}</b>\n\n"
    for i, (chat_id, username, priority, joined_at) in enumerate(members, 1):
        queue_text += f"{i}. @{username}\n"
    
    await message.answer(queue_text)

@dp.message(F.text.startswith('/delete_queue'))
async def delete_queue_handler(message: Message):
    if not is_admin(message.chat.id, message.from_user.username):
        await message.answer("<b>Access Denied</b>\n\nOnly admins can delete queues.")
        return
    
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.answer("<b>Usage:</b> <code>/delete_queue [queue_name]</code>\n\n<b>Example:</b> <code>/delete_queue Math</code>")
        return
    
    queue_name = parts[1].strip()
    success, msg = delete_queue(queue_name)
    
    if success:
        await message.answer(f"<b>Queue Deleted!</b>\n\nQueue '<b>{queue_name}</b>' and all its members have been removed.")
    else:
        await message.answer(f"<b>Error:</b> {msg}")

@dp.message(F.text.startswith('/set_priority'))
async def set_priority_handler(message: Message):
    if not is_admin(message.chat.id, message.from_user.username):
        await message.answer("<b>Access Denied</b>\n\nOnly admins can set priorities.")
        return
    
    parts = message.text.split(' ', 3)
    if len(parts) < 4:
        await message.answer("<b>Usage:</b> <code>/set_priority [queue_name] [username] [priority]</code>\n\n<b>Example:</b> <code>/set_priority Math john_doe 5</code>")
        return
    
    queue_name = parts[1].strip()
    username = parts[2].strip()
    try:
        priority = int(parts[3].strip())
    except ValueError:
        await message.answer("<b>Error:</b> Priority must be a number.")
        return
    
    success, msg = set_priority(queue_name, username, priority)
    await message.answer(f"<b>{'Success!' if success else 'Error:'}</b> {msg}")

@dp.message(F.text.startswith('/shuffle_queue'))
async def shuffle_queue_handler(message: Message):
    if not is_admin(message.chat.id, message.from_user.username):
        await message.answer("<b>Access Denied</b>\n\nOnly admins can shuffle queues.")
        return
    
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.answer("<b>Usage:</b> <code>/shuffle_queue [queue_name]</code>\n\n<b>Example:</b> <code>/shuffle_queue Math</code>")
        return
    
    queue_name = parts[1].strip()
    success, msg = shuffle_queue(queue_name)
    await message.answer(f"<b>{'Success!' if success else 'Error:'}</b> {msg}")

@dp.message(F.text == '/admin_info')
async def admin_info_handler(message: Message):
    if not is_admin(message.chat.id, message.from_user.username):
        await message.answer("<b>Access Denied</b>\n\nOnly admins can view admin information.")
        return
    
    admin_list = ", ".join(ADMIN_USERNAMES) if ADMIN_USERNAMES else "None configured"
    response = f"""
<b>Admin Configuration</b>

<b>Admin Commands:</b>

• <code>/create_queue [name]</code> - Create queue
• <code>/delete_queue [name]</code> - Delete queue
• <code>/set_priority [queue] [user] [priority]</code> - Set priority
• <code>/shuffle_queue [name]</code> - Shuffle queue randomly

<b>Admin Setup:</b>
Admins are configured via ADMIN_USERNAMES in .env file (comma-separated list)
See ENV_EXAMPLE.md for configuration details

<b>Environment Admins:</b> {admin_list}

<b>Your Username:</b> @{message.from_user.username or 'Not set'}

<b>Your Chat ID:</b> {message.chat.id}

<b>Admin Status:</b> ✅ You are an admin
"""
    await message.answer(response)

# Short Commands for Users
@dp.message(F.text.startswith('/join'))
async def join_short_handler(message: Message):
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.answer("<b>Usage:</b> <code>/join [queue_name]</code>\n\n<b>Example:</b> <code>/join Math</code>")
        return
    
    queue_name = parts[1].strip()
    username = message.from_user.username or message.from_user.full_name
    success, msg = join_queue(queue_name, message.chat.id, username)
    
    if success:
        await message.answer(f"<b>Successfully Joined!</b>\n\nYou have joined the '<b>{queue_name}</b>' queue.\n\nUse <code>/show {queue_name}</code> to see the current queue.")
    else:
        await message.answer(f"<b>Error:</b> {msg}")

@dp.message(F.text.startswith('/leave'))
async def leave_short_handler(message: Message):
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.answer("<b>Usage:</b> <code>/leave [queue_name]</code>\n\n<b>Example:</b> <code>/leave Math</code>")
        return
    
    queue_name = parts[1].strip()
    success, msg = leave_queue(queue_name, message.chat.id)
    
    if success:
        await message.answer(f"<b>Successfully Left!</b>\n\nYou have left the '<b>{queue_name}</b>' queue.")
    else:
        await message.answer(f"<b>Error:</b> {msg}")

@dp.message(F.text.startswith('/show'))
async def show_short_handler(message: Message):
    parts = message.text.split(' ', 1)
    if len(parts) < 2:
        await message.answer("<b>Usage:</b> <code>/show [queue_name]</code>\n\n<b>Example:</b> <code>/show Math</code>")
        return
    
    queue_name = parts[1].strip()
    members = get_queue_members(queue_name)
    
    if not members:
        await message.answer(f"<b>Queue: {queue_name}</b>\n\n<i>No members in this queue yet.</i>")
        return
    
    queue_text = f"<b>Queue: {queue_name}</b>\n\n"
    for i, (chat_id, username, priority, joined_at) in enumerate(members, 1):
        queue_text += f"{i}. @{username}\n"
    
    await message.answer(queue_text)

# Queue Buttons Command
@dp.message(F.text == '/queues')
async def queues_buttons_handler(message: Message):
    queues = get_all_queues()
    if not queues:
        await message.answer("<b>No queues available</b>\n\nAdmins can create queues using <code>/create_queue [name]</code>")
        return
    
    # Create buttons for each queue
    buttons = []
    for queue in queues:
        buttons.append([
            InlineKeyboardButton(text=f"Join {queue}", callback_data=f"join_{queue}"),
            InlineKeyboardButton(text=f"Show {queue}", callback_data=f"show_{queue}"),
            InlineKeyboardButton(text=f"Leave {queue}", callback_data=f"leave_{queue}")
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("<b>Queue Management</b>\n\nSelect an action for any queue:", reply_markup=keyboard)

# Queue Button Callbacks
@dp.callback_query(F.data.startswith('join_'))
async def join_queue_callback(callback: CallbackQuery):
    queue_name = callback.data.replace('join_', '')
    username = callback.from_user.username or callback.from_user.full_name
    success, msg = join_queue(queue_name, callback.message.chat.id, username)
    
    if success:
        await callback.answer(f"✅ Joined {queue_name} queue!")
    else:
        await callback.answer(f"❌ {msg}")
    
    # Update the message to show current queue
    members = get_queue_members(queue_name)
    if members:
        queue_text = f"<b>Queue: {queue_name}</b>\n\n"
        for i, (chat_id, username, priority, joined_at) in enumerate(members, 1):
            queue_text += f"{i}. @{username}\n"
    else:
        queue_text = f"<b>Queue: {queue_name}</b>\n\n<i>No members in this queue yet.</i>"
    
    await callback.message.edit_text(queue_text)

@dp.callback_query(F.data.startswith('show_'))
async def show_queue_callback(callback: CallbackQuery):
    queue_name = callback.data.replace('show_', '')
    members = get_queue_members(queue_name)
    
    if not members:
        queue_text = f"<b>Queue: {queue_name}</b>\n\n<i>No members in this queue yet.</i>"
    else:
        queue_text = f"<b>Queue: {queue_name}</b>\n\n"
        for i, (chat_id, username, priority, joined_at) in enumerate(members, 1):
            queue_text += f"{i}. @{username}\n"
    
    await callback.message.edit_text(queue_text)
    await callback.answer()

@dp.callback_query(F.data.startswith('leave_'))
async def leave_queue_callback(callback: CallbackQuery):
    queue_name = callback.data.replace('leave_', '')
    success, msg = leave_queue(queue_name, callback.message.chat.id)
    
    if success:
        await callback.answer(f"✅ Left {queue_name} queue!")
    else:
        await callback.answer(f"❌ {msg}")
    
    # Update the message to show current queue
    members = get_queue_members(queue_name)
    if members:
        queue_text = f"<b>Queue: {queue_name}</b>\n\n"
        for i, (chat_id, username, priority, joined_at) in enumerate(members, 1):
            queue_text += f"{i}. @{username}\n"
    else:
        queue_text = f"<b>Queue: {queue_name}</b>\n\n<i>No members in this queue yet.</i>"
    
    await callback.message.edit_text(queue_text)

# Command handlers for bot menu
@dp.message(F.text == '/deadlines')
async def deadlines_command_handler(message: Message):
    text = all_deadlines(get_all_records())
    if text.strip():
        response = f"<b>Your Deadlines:</b>\n\n{text}\n\n<i>Reminders sent daily at 12:00 PM</i>"
    else:
        response = "<b>Your Deadlines:</b>\n\n<i>No deadlines found! You're all caught up!</i>\n\n<i>Reminders sent daily at 12:00 PM</i>"
    await message.answer(response, disable_web_page_preview=True)

@dp.message(F.text == '/notify')
async def notify_command_handler(message: Message, state: FSMContext):
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
    await message.answer(notification_text)
    await state.set_state(NotificationForm.waiting_for_notification)

@dp.message(F.text == '/pass')
async def pass_command_handler(message: Message):
    text = all_deadlines(get_all_records(),['Name','Pass'])
    if text.strip():
        response = f"<b>Works to Pass:</b>\n\n{text}\n\n<i>Keep up the good work!</i>"
    else:
        response = "<b>Works to Pass:</b>\n\n<i>No pending works to pass! Great job!</i>"
    await message.answer(response)

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
        role = 'admin' if message.from_user.username in ADMIN_USERNAMES else 'user'
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
    if is_admin(message.chat.id, message.from_user.username):
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
    # Set up bot commands menu
    await setup_bot_commands()
    
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_deadlines, "cron", hour=12, minute=0)
    scheduler.start()
    await dp.start_polling(bot)

if __name__=='__main__':
    con = sqlite3.connect(DATABASE_PATH)
    cursor = con.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER UNIQUE,
        username TEXT,
        role TEXT
    )
''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queue_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        queue_id INTEGER NOT NULL,
        chat_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        priority INTEGER DEFAULT 0,
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (queue_id) REFERENCES queues (id) ON DELETE CASCADE,
        UNIQUE(queue_id, chat_id)
    )
''')
    
    con.commit()
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())