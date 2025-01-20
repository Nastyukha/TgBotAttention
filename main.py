from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
import asyncio
from config import API_TOKEN
from database import init_db
from commands import bot_commands
from handlers import (
    cmd_start, process_name, register_handlers
)
from states import Registration, TestStates

# Инициализация бота и диспетчера
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Регистрация обработчиков
dp.message.register(cmd_start, Command("start"))
dp.message.register(process_name, Registration.waiting_for_name)

# Регистрация обработчиков для callback_query
register_handlers(dp)

# Запуск бота
async def main():
    init_db()
    await bot_commands(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())