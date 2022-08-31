import asyncio
import nest_asyncio
import logging

from aiogram import executor
from asyncpg import UniqueViolationError, UndefinedTableError
import handlers, filters, middlewares
from data.config import ADMINS
from loader import dp, db, bot
from utils.parser_api.parser_1 import control_ratings
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands


async def on_startup(dispatcher):
    await set_default_commands(dispatcher)


async def schedule_notify():
    await db.create_table_goods()
    await db.create_table_parse()
    try:
        await db.insert_parse(boolean=False)
    except UniqueViolationError:
        pass
    while True:
        data = await db.select_parse()
        await asyncio.sleep(data[1])
        data = await db.select_parse()
        if data[0]:
            nest_asyncio.apply()
            loop = asyncio.get_running_loop()
            goods = await db.select_goods_active()
            num = len(goods)//3
            events = [
                asyncio.ensure_future(control_ratings(goods[:num])),
                asyncio.ensure_future(control_ratings(goods[num:num+num])),
                asyncio.ensure_future(control_ratings(goods[num+num:]))
            ]
            loop.run_until_complete(asyncio.gather(*events))
        await bot.send_message(ADMINS[0], 'Finished All')


if __name__ == '__main__':
    dp.loop.create_task(schedule_notify())
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)
