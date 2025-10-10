# Deadline Checker Bot

A Telegram bot that helps you manage and track deadlines by integrating with Google Sheets. The bot automatically sends reminders and manages deadline data.

## Features

- **Automated Reminders**: Sends notifications at **12:00 PM** daily for:
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
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Google Sheets API credentials
- Docker (optional, for containerized deployment)

## Setup

### 1. Environment Setup

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_telegram_bot_token_here
```

### 2. Google Sheets Setup

1. Create a Google Sheet named "Deadline_checker"
2. Set up the following columns in the first row:

   - `Deadline` (format: DD.MM.YYYY)
   - `Name` (task/subject description)
   - `Link` (optional URL)
   - `Pass` (optional additional field)

3. Download Google Sheets API credentials:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable Google Sheets API
   - Create credentials (Service Account)
   - Download the JSON file
   - Place it at `.config/gspread/credentials.json`

### 3. Installation

#### Option A: Local Installation

```bash
# Clone the repository
git clone <repository-url>
cd Deadline_checker

# Install dependencies
pip install -r requirements.txt

# Run the bot
python main.py
```

#### Option B: Docker Installation

```bash
# Build and run with Docker Compose
docker-compose up --build
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

The bot automatically sends reminders at **12:00 PM** daily:

- **7 days before**: "Reminder: 1 week left until [date] — [task]"
- **1 day before**: "Reminder: Tomorrow is the deadline [date] — [task]"
- **On deadline day**: "Deadline today: [date] — [task]"
- **1 day after**: "Reminder: Yesterday was the deadline [date] — [task]. It will delete now"

After the deadline passes, the row is automatically deleted from the Google Sheet.

## Configuration

### Reminder Schedule

Reminders are sent daily at **12:00 PM** (configured in `main.py` line 174):

```python
scheduler.add_job(check_deadlines, "cron", hour=11, minute=0)  # 12:00 PM
```

### Admin Access

The user with username `Sergio_Suprun` automatically gets admin privileges. Other users can be granted admin access by modifying the code.

## File Structure

```
Deadline_checker/
├── main.py              # Main bot logic and handlers
├── sheets.py            # Google Sheets integration
├── utilities.py         # Helper functions and utilities
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile          # Docker image configuration
├── bot_data.db         # SQLite database (auto-created)
└── README.md           # This file
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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the license file for more details.

## Support

For issues and questions, please create an issue in the repository or contact the maintainer.
