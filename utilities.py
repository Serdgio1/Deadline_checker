from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup



def get_keyboard():
        menu_keyboard = InlineKeyboardMarkup(
             inline_keyboard=[
                [InlineKeyboardButton(text='Deadlines',callback_data='deadlines')],
                [InlineKeyboardButton(text='See my points',callback_data='points')]
            ]
        )
        return menu_keyboard

def all_deadlines(records):
    res = ''
    count = 0
    for record in records:
          count += 1
          res += f'{count} {str(record['Deadline'])} {record['Name']} {record['Link']}\n'
    return res

