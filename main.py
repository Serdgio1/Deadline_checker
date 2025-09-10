import gspread
from google.auth.exceptions import TransportError

gc = gspread.service_account(filename='.config/gspread/credentials.json')

sh = gc.open("Deadline_checker")

worksheet = sh.sheet1

def add_row(retries=3):
    for attempt in range(retries):
        try:
            new_row_data = ["Value 1", "Value 2", "Value 3", 123]
            worksheet.append_row(new_row_data)
            print(f"Row appended to 'Deadline_checker'")
            return True
        except (gspread.exceptions.APIError, TransportError) as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                pass
            else:
                return False


add_row()