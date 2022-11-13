from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import ReplyKeyboardRemove

from keyboards.inline.inline_keyboards import main_menu
from loader import dp, db
from utils.parser_api.parser_1 import parse_all_goods


@dp.message_handler(Command('clear'))
async def scan(message: types.Message):
    await db.delete_goods()
    await message.answer('Товары успешно удалены!')


@dp.message_handler(Command('g'))
async def scan(message: types.Message):
    await message.answer_photo('p1.png')


@dp.message_handler(Command('scan'))
async def scan(message: types.Message):
    await message.answer('Сканирование начался...')
    added = await parse_all_goods()
    await message.answer(f"{added} товары добавлено✅")
    await message.answer('Введите нужный вам команду', reply_markup=main_menu)


@dp.message_handler(Command('stop'))
async def scan(message: types.Message):
    await db.update_parse_bool(boolean=False)
    await message.answer(f"Отслеживание остановлено!")
    await message.answer('Введите нужный вам команду', reply_markup=main_menu)


@dp.message_handler(Command('run'))
async def scan(message: types.Message):
    await db.update_parse_bool(boolean=True)
    await message.answer(f"Отслеживание начинался!")
    await message.answer('Введите нужный вам команду', reply_markup=main_menu)


@dp.message_handler(Command('time'))
async def scan(message: types.Message, state: FSMContext):
    await message.answer(f"Введите время на секундах", reply_markup=ReplyKeyboardRemove())
    await state.set_state('from_time')


@dp.message_handler(state='from_time')
async def scan(message: types.Message, state: FSMContext):
    await db.update_parse_time(time=int(message.text.strip()))
    await message.answer(f"Время паузы изменен!")
    await message.answer('Введите нужный вам команду', reply_markup=main_menu)
    await state.finish()


