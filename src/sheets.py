import gspread
from google.auth.exceptions import TransportError
from datetime import datetime
from config import CREDENTIALS_FILE

gc = gspread.service_account(filename=CREDENTIALS_FILE)
sh = gc.open("Deadline_checker")
worksheet = sh.sheet1

def add_row(new_row_data, retries=3):
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