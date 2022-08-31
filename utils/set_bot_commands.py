from aiogram import types


async def set_default_commands(dp):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "Запустить бота"),
            types.BotCommand("scan", "Сканировать"),
            types.BotCommand("manage", "Управлять товары"),
            types.BotCommand("time", "Установить время паузы"),
            types.BotCommand("run", "Начать работу"),
            types.BotCommand("stop", "Остановить работу"),
        ]
    )
