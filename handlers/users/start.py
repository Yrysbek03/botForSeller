from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart

from keyboards.inline.inline_keyboards import main_menu
from loader import dp


@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    await message.answer('Введите нужный вам команду', reply_markup=main_menu)
