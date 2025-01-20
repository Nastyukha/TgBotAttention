from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncio
from config import API_TOKEN
from database import init_db
from commands import bot_commands
from handlers import (
    cmd_start, process_name, register_handlers, send_daily_notifications
)
from states import Registration
from middleware import RegistrationMiddleware

# Инициализация бота и диспетчера
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Добавление Middleware
dp.message.middleware(RegistrationMiddleware())
dp.callback_query.middleware(RegistrationMiddleware())

# Регистрация обработчиков
dp.message.register(cmd_start, Command("start"))
dp.message.register(process_name, Registration.waiting_for_name)

# Регистрация обработчиков для callback_query
register_handlers(dp)

# Запуск бота
async def main():
    init_db()

    # Инициализация планировщика
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_daily_notifications, 'cron', hour=9, minute=0, args=[bot])
    scheduler.start()

    await bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())