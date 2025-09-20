from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup



def get_keyboard(buttons):
    keyboard = []
    for btn in buttons:
        if isinstance(btn, (list, tuple)) and len(btn) == 2:
            text, cb_data = btn
        else:
            text, cb_data = str(btn), str(btn)
        keyboard.append([InlineKeyboardButton(text=text, callback_data=cb_data)])
    menu_keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return menu_keyboard

def all_deadlines(records):
    res = ''
    count = 0
    for record in records:
          count += 1
          res += f"{count}. {str(record['Deadline'])} {record['Name']} {record['Link']}\n"
    return res

