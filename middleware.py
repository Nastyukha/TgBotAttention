from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from database import cursor, conn
from states import Registration

class RegistrationMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: types.Message | types.CallbackQuery, data: dict):
        user_id = event.from_user.id

        # Получаем текущее состояние пользователя
        current_state = await data["state"].get_state()

        # Пропускаем команду /start и процесс регистрации
        if isinstance(event, types.Message) and (event.text == "/start" or current_state == Registration.waiting_for_name):
            return await handler(event, data)

        # Проверяем, зарегистрирован ли пользователь
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        if user is None and not isinstance(event, types.CallbackQuery):
            await event.answer("Пожалуйста, зарегистрируйтесь с помощью команды /start.")
            return

        # Записываем действие пользователя в базу данных
        action = event.text if isinstance(event, types.Message) else event.data
        cursor.execute('''
        INSERT INTO user_actions (user_id, action, timestamp)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, action))
        conn.commit()

        return await handler(event, data)