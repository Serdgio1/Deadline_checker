import gspread
from google.auth.exceptions import TransportError
from datetime import datetime
from os import getenv

gc = None
sh = None
worksheet = None

def _init_sheets():
    """Initialize Google Sheets connection lazily"""
    global gc, sh, worksheet
    if gc is None:
        credentials_file = getenv("CREDENTIALS_FILE")
        if not credentials_file:
            raise ValueError("CREDENTIALS_FILE environment variable is not set")
        gc = gspread.service_account(filename=credentials_file)
sh = gc.open("Deadline_checker")
worksheet = sh.sheet1

def add_row(new_row_data, retries=3):
    _init_sheets()
    for attempt in range(retries):
        try:
            worksheet.append_row(new_row_data)
            print(f"Row appended to 'Deadline_checker'")
            return True
        except (gspread.exceptions.APIError, TransportError) as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                pass
            else:
                return False

def get_all_records(retries=3):
    _init_sheets()
    for attempt in range(retries):
        try:
            records = worksheet.get_all_records()
            return sorted(records, key=lambda r: datetime.strptime(r["Deadline"], "%d.%m.%Y"))
        except (gspread.exceptions.APIError, TransportError) as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                pass
            else:
                return None

def delete_row(row_number, retries=3):
    _init_sheets()
    for attempt in range(retries):
        try:
            worksheet.delete_rows(row_number)
            print(f"Row {row_number} deleted from 'Deadline_checker'")
            return True
        except (gspread.exceptions.APIError, TransportError) as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                pass
            else:
                return False