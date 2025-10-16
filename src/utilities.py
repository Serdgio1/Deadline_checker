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

def all_deadlines(records, fields=['Deadline', 'Name', 'Link']):
    res = ''
    count = 1
    for record in records:
        values = []
        f = 1
        for field in fields:
            if record.get(field, '') == '':
                f = 0
                continue
            values.append(str(record.get(field, '')))
        if f == 1:
            res += f"{count}. {' '.join(values)}\n"
            count += 1
    return res