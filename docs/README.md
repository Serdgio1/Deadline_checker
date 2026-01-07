# Deadline Checker Bot

A Telegram bot that helps you manage and track deadlines by integrating with Google Sheets. The bot automatically sends reminders and manages deadline data.

## Features

- **Automated Reminders**: Sends notifications at 12:00 PM daily for:
  - 7 days before deadline
  - 1 day before deadline
  - On the deadline day
  - 1 day after deadline (with deletion notice)
- **Google Sheets Integration**: Automatically syncs with Google Sheets for deadline management
- **User Management**: Role-based access with admin and user permissions
- **Deadline Management**: Add, view, and automatically delete expired deadlines
- **Docker Support**: Easy deployment with Docker and Docker Compose

## Prerequisites

- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Google Sheets API credentials
- Docker (optional, for containerized deployment)

## Setup (local)

1) `.env` in project root:
```env
BOT_TOKEN=your_telegram_bot_token_here
CREDENTIALS_FILE=.config/gspread/credentials.json
DATABASE_PATH=data/bot_data.db
```

2) Google Sheets:
   - Create sheet `Deadline_checker` with columns: `Deadline`, `Name`, `Link`, `Pass`
   - Download service-account JSON and place at `.config/gspread/credentials.json`

3) Install & run:
```bash
pip install -r requirements.txt
python -m src.main
```

## Setup (Docker)

```bash
docker-compose up --build -d   # build + start
docker-compose logs -f         # tail logs
docker-compose down            # stop
```

## Usage

### Bot Commands

- `/start` - Initialize the bot and get the main menu
- `/add_deadline` - Add a new deadline (admin only)
- `/all` - Send message to all users (admin only)

### Main Menu Options

- **Deadlines** - View all current deadlines
- **See my points** - View points (feature coming soon)
- **Notifications** - Enable/disable notifications
- **Pass** - View work to pass

### Adding Deadlines (Admin)

Use the `/add_deadline` command and follow the format:

```
DD.MM.YYYY Subject Link
```

Example:

```
25.12.2024 Christmas Assignment https://example.com
```

### Notification System

The bot automatically sends reminders at 12:00 PM daily:

- **7 days before**: "Weekly Reminder: 1 week left until [date] — [task]"
- **1 day before**: "Final Reminder: Tomorrow is the deadline [date] — [task]"
- **On deadline day**: "DEADLINE TODAY: [date] — [task]"
- **1 day after**: "Deadline Expired: Yesterday was the deadline [date] — [task]. It will delete now"

After the deadline passes, the row is automatically deleted from the Google Sheet.

## Configuration

### Reminder Schedule

Reminders are sent daily at 12:00 PM (configured in `main.py`):

```python
scheduler.add_job(check_deadlines, "cron", hour=12, minute=0)
```

### Admin Access

The user with username `Sergio_Suprun` automatically gets admin privileges. Other users can be granted admin access by modifying the code.

## File Structure

```
Deadline_checker/
├── src/
│   ├── main.py        # bot logic and handlers
│   ├── sheets.py      # Google Sheets integration
│   ├── utilities.py   # keyboard helpers
│   └── config.py      # env loader
├── requirements.txt   # Python deps
├── Dockerfile
├── docker-compose.yml
├── ENV_EXAMPLE.md
└── docs/
    └── README.md      # this file
```

## Database Schema

The bot uses SQLite with the following table structure:

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER UNIQUE,
    username TEXT,
    role TEXT
)
```

## Troubleshooting

### Common Issues

1. **Google Sheets API Errors**: Ensure your credentials file is correctly placed and the service account has access to the spreadsheet
2. **Bot Token Issues**: Verify your BOT_TOKEN in the `.env` file
3. **Permission Errors**: Check that the bot has proper permissions in your Google Sheet

### Logs

The bot logs important events to stdout. Check the console output for debugging information.
