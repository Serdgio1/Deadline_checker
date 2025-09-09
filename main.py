import gspread

gc = gspread.service_account(filename='.config/gspread/credentials.json')

sh = gc.open("Deadline_checker")

worksheet = sh.sheet1

# Define the row data as a list
new_row_data = ["Value 1", "Value 2", "Value 3", 123]

# Append the row to the worksheet
worksheet.append_row(new_row_data)

print(f"Row '{new_row_data}' appended to 'Deadline_checker'")

