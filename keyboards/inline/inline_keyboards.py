from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton('/scan'),
            KeyboardButton('/manage')
        ],
        [
            KeyboardButton('/stop'),
            KeyboardButton('/run')
        ],
        [
            KeyboardButton('/time')
        ]
    ], resize_keyboard=True
)

manage_good = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton('LIMIT'),
            KeyboardButton('MINUS')
        ],
        [
            KeyboardButton('ACTIVATE'),
            KeyboardButton('DEACTIVATE')
        ],
        [
            KeyboardButton('❌DELETE🗑'),
            KeyboardButton('НАЗАД')
        ]
    ], resize_keyboard=True
)
