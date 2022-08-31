from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.exceptions import MessageTextIsEmpty

from keyboards.inline.inline_keyboards import main_menu, manage_good
from loader import dp, db


def info(good, table=False) -> str:
    return f'<b>id</b>: {good[0]} <a href="{good[2]}">{good[1]}</a> limit: {good[4]} —{good[5]} {"Активен" if good[6] else "Неактивен" }\n'


@dp.message_handler(Command('manage'))
async def scan(message: types.Message, state: FSMContext):
    try:
        text = ''
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for good in await db.select_goods():
            text += info(good)
            if len(text) > 5000:
                await message.answer(text)
                text = ''
            markup.insert(KeyboardButton(str(good[0])))
        markup.insert(KeyboardButton('НАЗАД'))
        await message.answer(text, reply_markup=markup)
        await message.answer('Выберите id товара, который хотите изменить')
        await state.set_state('from_manage')
    except MessageTextIsEmpty as e:
        await message.answer('Сперва нужно сканировать товары!\nДля этого нажмите /scan', reply_markup=main_menu)


@dp.message_handler(state='from_manage')
async def manage(message: types.Message, state: FSMContext):
    if message.text == 'НАЗАД':
        await message.answer('Введите нужный вам команду', reply_markup=main_menu)
        await state.finish()
    else:
        await state.update_data(good_id=message.text)
        good = await db.select_good(good_id=int(message.text))
        await message.answer(info(good),
                             reply_markup=manage_good)
        await state.set_state('manage_good')


@dp.message_handler(state='manage_good')
async def manage(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if message.text == 'НАЗАД':
        text = ''
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        for good in await db.select_goods():
            text += info(good)
            if len(text) > 5000:
                await message.answer(text)
                text = ''
            markup.insert(KeyboardButton(str(good[0])))
        markup.insert(KeyboardButton('НАЗАД'))
        await message.answer(text, reply_markup=markup)
        await message.answer('Выберите id товара, который хотите изменить')
        await state.set_state('from_manage')
    elif message.text == 'LIMIT':
        await message.answer('Введите минимальную цену')
        await state.set_state('manage_good_limit')
    elif message.text == 'MINUS':
        await message.answer('Введите разницу')
        await state.set_state('manage_good_minus')
    elif message.text == 'ACTIVATE':
        await db.update_good(good_id=int(data['good_id']), is_active=True)
        await message.answer('товар активирован!')
        good = await db.select_good(good_id=int(data['good_id']))
        await message.answer(info(good),
                             reply_markup=manage_good)
        await state.set_state('manage_good')
    elif message.text == 'DEACTIVATE':
        await db.update_good(good_id=int(data['good_id']), is_active=False)
        await message.answer('товар деактивирован!')
        good = await db.select_good(good_id=int(data['good_id']))
        await message.answer(info(good),
                             reply_markup=manage_good)
        await state.set_state('manage_good')
    elif message.text == '❌DELETE🗑':
        await db.delete_good(int(data['good_id']))


@dp.message_handler(state='manage_good_limit')
async def manage(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.update_good(good_id=int(data['good_id']), minimum=int(message.text.strip()))
    await message.answer('✅')
    good = await db.select_good(good_id=int(data['good_id']))
    await message.answer(info(good),
                         reply_markup=manage_good)
    await state.set_state('manage_good')


@dp.message_handler(state='manage_good_minus')
async def manage(message: types.Message, state: FSMContext):
    data = await state.get_data()
    await db.update_good(good_id=int(data['good_id']), minus=int(message.text.strip()))
    await message.answer('✅')
    good = await db.select_good(good_id=int(data['good_id']))
    await message.answer(info(good),
                         reply_markup=manage_good)
    await state.set_state('manage_good')
