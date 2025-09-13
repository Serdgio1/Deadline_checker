import gspread
from google.auth.exceptions import TransportError

gc = gspread.service_account(filename='.config/gspread/credentials.json')
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
            return records
        except (gspread.exceptions.APIError, TransportError) as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                pass
            else:
                return None