from aiogram import types, F, Router
from aiogram import Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
from database import cursor, conn
from keyboards import get_main_menu_keyboard, get_return_to_main_menu_keyboard, get_choose_test_keyboard, get_confirmation_keyboard
from gigachat_api import generate_attention_test
import logging
from states import FeedbackStates, NotificationStates
from aiogram.fsm.state import State, StatesGroup

logger = logging.getLogger(__name__)

# Состояния для регистрации
class Registration(StatesGroup):
    waiting_for_name = State()

# Состояния для тестов
class TestStates(StatesGroup):
    waiting_for_answer = State()

# Обработчик команды /start
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    logger.info(f"Пользователь {user_id} начал работу с ботом.")
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()

    if user is None:
        await message.answer("Привет! Давай зарегистрируемся. Введи своё имя:")
        await state.set_state(Registration.waiting_for_name)
    else:
        await show_main_menu(message)

# Обработчик ввода имени
async def process_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.text
    logger.info(f"Пользователь {user_id} зарегистрировался с именем {name}.")

    cursor.execute('INSERT INTO users (user_id, name) VALUES (?, ?)', (user_id, name))
    conn.commit()

    await message.answer(f"Спасибо, {name}! Теперь ты зарегистрирован.")
    await show_main_menu(message)
    await state.clear()

# Функция для отображения главного меню
async def show_main_menu(message: types.Message | CallbackQuery):
    keyboard = get_main_menu_keyboard()

    text = 'Главное меню:'

    if isinstance(message, CallbackQuery):
        await message.message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

# Регистрация обработчиков

async def start_choosen_test(callback: CallbackQuery, state: FSMContext):
    """
    Начинает тест в зависимости от выбранного типа.
    """

    # Определяем user_id
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} начал тест.")

    # Получаем тип теста из callback_data
    action, test_type = callback.data.split(":")
    logger.info(f"Тип теста: {test_type}")

    try:
        # Генерируем тест в зависимости от типа
        if test_type == "word_count":
            question, correct_answer = generate_attention_test("посчитать слова")
        elif test_type == "letter_count":
            question, correct_answer = generate_attention_test("посчитать буквы")
        elif test_type == "extra_word":
            question, correct_answer = generate_attention_test("найти лишнее слово")
        else:
            raise ValueError("Неизвестный тип теста")

        # Сохраняем правильный ответ в состоянии
        await state.update_data(correct_answer=correct_answer)

        # Форматируем задание по шаблону
        task_text = f"Задание: {question}\nФормат ответа: отправьте только цифру."
        await callback.message.answer(task_text)

        # Переходим в состояние ожидания ответа
        await state.set_state(TestStates.waiting_for_answer)
    except Exception as e:
        logger.error(f"Ошибка при генерации теста: {e}")
        await callback.message.answer(f"Произошла ошибка: {e}")
        await show_main_menu(callback)
        await state.clear()

async def check_test_answer(message: types.Message, state: FSMContext):
    """
    Проверяет ответ пользователя на тест и сохраняет результат.
    """
    user_id = message.from_user.id
    user_answer = message.text
    logger.info(f"Пользователь {user_id} отправил ответ: {user_answer}.")

    # Получаем данные из состояния
    data = await state.get_data()
    correct_answer = data.get("correct_answer")
    test_types = data.get("test_types", [])
    current_test_index = data.get("current_test_index", 0)
    correct_answers_count = data.get("correct_answers_count", 0)  # Получаем счетчик

    # Определяем тип текущего теста
    test_type = test_types[current_test_index] if test_types else "single_test"

    # Проверяем ответ
    try:
        if user_answer.strip() == correct_answer.strip():
            result = "Правильно"
            correct_answers_count += 1  # Увеличиваем счетчик
            await message.answer("✅ Правильно! Молодец!")
        else:
            result = f"Неправильно. Правильный ответ: {correct_answer}"
            await message.answer(f"❌ Неправильно. Правильный ответ: {correct_answer}")
    except Exception as e:
        logger.error(f"Ошибка при проверке ответа: {e}")
        await message.answer(f"Произошла ошибка: {e}")
        result = "Ошибка"

    # Сохраняем результат теста в базу данных
    cursor.execute('''
    INSERT INTO test_history (user_id, test_type, result)
    VALUES (?, ?, ?)
    ''', (user_id, test_type, result))
    conn.commit()

    # Обновляем состояние с новым значением счетчика
    await state.update_data(correct_answers_count=correct_answers_count)

    # Проверяем, есть ли еще тесты для прохождения
    if test_types:  # Если это часть прохождения всех тестов
        await state.update_data(current_test_index=current_test_index + 1)
        await send_next_test(message, state)
    else:  # Если это одиночный тест
        await show_main_menu(message)
        await state.clear()

async def start_complex_test(callback: CallbackQuery, state: FSMContext):
    """
    Начинает поочередное выполнение всех тестов.
    """
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} начал выполнение всех тестов.")

    # Список типов тестов
    test_types = ["word_count", "letter_count", "extra_word"]

    # Сохраняем список тестов и текущий индекс в состоянии
    await state.update_data(test_types=test_types, current_test_index=0)

    # Запускаем первый тест
    await send_next_test(callback, state)

async def send_next_test(update: types.Message | types.CallbackQuery, state: FSMContext):
    """
    Отправляет следующий тест из списка и сохраняет статистику после завершения.
    """
    # Получаем данные из состояния
    data = await state.get_data()
    test_types = data.get("test_types", [])
    current_test_index = data.get("current_test_index", 0)
    correct_answers_count = data.get("correct_answers_count", 0)  # Получаем счетчик

    # Проверяем, все ли тесты пройдены
    if current_test_index >= len(test_types):
        user_id = update.from_user.id
        total_tests = len(test_types)

        # Сохраняем статистику в базу данных
        cursor.execute('''
        INSERT OR REPLACE INTO test_statistics (user_id, total_tests, correct_answers)
        VALUES (?, COALESCE((SELECT total_tests FROM test_statistics WHERE user_id = ?), 0) + ?,
                      COALESCE((SELECT correct_answers FROM test_statistics WHERE user_id = ?), 0) + ?)
        ''', (user_id, user_id, total_tests, user_id, correct_answers_count))
        conn.commit()

        # Выводим сообщение о завершении тестов
        if isinstance(update, types.CallbackQuery):
            await update.message.answer("🎉 Вы прошли все тесты! Возвращаюсь в главное меню.")
            await show_main_menu(update)
        else:
            await update.answer("🎉 Вы прошли все тесты! Возвращаюсь в главное меню.")
            await show_main_menu(update)
        await state.clear()
        return

    # Получаем текущий тип теста
    test_type = test_types[current_test_index]
    logger.info(f"Пользователь {update.from_user.id} начинает тест: {test_type}")

    try:
        # Генерируем тест в зависимости от типа
        if test_type == "word_count":
            question, correct_answer = generate_attention_test("посчитать слова")
        elif test_type == "letter_count":
            question, correct_answer = generate_attention_test("посчитать буквы")
        elif test_type == "extra_word":
            question, correct_answer = generate_attention_test("найти лишнее слово")
        else:
            raise ValueError("Неизвестный тип теста")

        # Сохраняем правильный ответ в состоянии
        await state.update_data(correct_answer=correct_answer)

        # Форматируем задание по шаблону
        task_text = f"Задание: {question}\nФормат ответа: отправьте только цифру."
        if isinstance(update, types.CallbackQuery):
            await update.message.answer(task_text)
        else:
            await update.answer(task_text)

        # Переходим в состояние ожидания ответа
        await state.set_state(TestStates.waiting_for_answer)
    except Exception as e:
        logger.error(f"Ошибка при генерации теста: {e}")
        if isinstance(update, types.CallbackQuery):
            await update.message.answer(f"Произошла ошибка: {e}")
            await show_main_menu(update)
        else:
            await update.answer(f"Произошла ошибка: {e}")
            await show_main_menu(update)
        await state.clear()

async def go_to_new_keyboard(callback: CallbackQuery):
    """
    Обрабатывает нажатие кнопки "Тренировка с заданиями по выбору" и переключает клавиатуру.
    """
    # Получаем новую клавиатуру
    new_keyboard = get_choose_test_keyboard()

    # Редактируем текущее сообщение, заменяя клавиатуру
    await callback.message.edit_reply_markup(reply_markup=new_keyboard)

async def show_test_history(callback: CallbackQuery):
    """
    Показывает историю прохождения тестов пользователя.
    """
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} запросил историю тестов.")

    # Получаем историю тестов из базы данных
    cursor.execute('''
    SELECT test_type, result, timestamp FROM test_history
    WHERE user_id = ?
    ORDER BY timestamp DESC
    ''', (user_id,))
    history = cursor.fetchall()

    if not history:
        await callback.message.answer("История тестов пуста.")
        return

    # Формируем текст для вывода истории
    history_text = "📜 История тестов:\n\n"
    for entry in history:
        test_type, result, timestamp = entry
        history_text += f"📅 {timestamp}\n"
        history_text += f"🔍 Тип теста: {test_type}\n"
        history_text += f"📝 Результат: {result}\n\n"

    await callback.message.answer(history_text)

async def show_statistics(callback: CallbackQuery):
    """
    Показывает статистику пользователя по всем пройденным тестам.
    """
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} запросил статистику.")

    # Получаем статистику из базы данных
    cursor.execute('''
    SELECT total_tests, correct_answers FROM test_statistics
    WHERE user_id = ?
    ''', (user_id,))
    stats = cursor.fetchone()

    if not stats:
        await callback.message.answer("Статистика отсутствует. Пройдите хотя бы один комплексный тест.")
        return

    total_tests, correct_answers = stats

    # Формируем текст для вывода статистики
    stats_text = (
        f"📊 Ваша статистика:\n"
        f"📅 Всего пройдено тестов: {total_tests}\n"
        f"✅ Правильных ответов: {correct_answers}\n"
        f"📈 Процент правильных ответов: {correct_answers / total_tests * 100:.2f}%"
    )

    await callback.message.answer(stats_text)

async def delete_history(callback: CallbackQuery):
    """
    Удаляет историю тестов пользователя.
    """
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} запросил удаление истории.")

    # Удаляем историю тестов
    cursor.execute('DELETE FROM test_history WHERE user_id = ?', (user_id,))
    conn.commit()

    await callback.message.answer("🗑️ История тестов успешно удалена.")
    await show_main_menu(callback)

async def delete_statistics(callback: CallbackQuery):
    """
    Удаляет статистику пользователя.
    """
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} запросил удаление статистики.")

    # Удаляем статистику
    cursor.execute('DELETE FROM test_statistics WHERE user_id = ?', (user_id,))
    conn.commit()

    await callback.message.answer("🗑️ Статистика успешно удалена.")
    await show_main_menu(callback)

async def confirm_delete(callback: CallbackQuery):
    """
    Обрабатывает подтверждение удаления.
    """
    action = callback.data.split("_")[1]  # Получаем действие (history или statistics)

    if action == "history":
        await delete_history(callback)
    elif action == "statistics":
        await delete_statistics(callback)

async def cancel_delete(callback: CallbackQuery):
    """
    Отменяет удаление и возвращает пользователя в главное меню.
    """
    await callback.message.answer("❌ Удаление отменено.")
    await show_main_menu(callback)

async def request_delete_history(callback: CallbackQuery):
    """
    Запрашивает подтверждение для удаления истории.
    """
    await callback.message.answer(
        "⚠️ Вы уверены, что хотите удалить историю тестов?",
        reply_markup=get_confirmation_keyboard("history")
    )

async def request_delete_statistics(callback: CallbackQuery):
    """
    Запрашивает подтверждение для удаления статистики.
    """
    await callback.message.answer(
        "⚠️ Вы уверены, что хотите удалить статистику?",
        reply_markup=get_confirmation_keyboard("statistics")
    )

async def save_feedback(user_id: int, feedback_text: str):
    """
    Сохраняет отзыв пользователя в базу данных вместе с именем пользователя.
    """
    # Получаем имя пользователя из таблицы users
    cursor.execute('SELECT name FROM users WHERE user_id = ?', (user_id,))
    user_name = cursor.fetchone()[0]  # Получаем имя из результата запроса

    # Сохраняем отзыв с именем пользователя
    cursor.execute('''
    INSERT INTO feedback (user_id, user_name, feedback_text)
    VALUES (?, ?, ?)
    ''', (user_id, user_name, feedback_text))
    conn.commit()

async def request_feedback(callback: CallbackQuery, state: FSMContext):
    """
    Запрашивает отзыв у пользователя.
    """
    await callback.message.answer("📝 Пожалуйста, напишите ваш отзыв:")
    await state.set_state(FeedbackStates.waiting_for_feedback)

async def process_feedback(message: types.Message, state: FSMContext):
    """
    Обрабатывает отзыв пользователя и сохраняет его в базу данных.
    """
    user_id = message.from_user.id
    feedback_text = message.text

    # Сохраняем отзыв в базу данных
    await save_feedback(user_id, feedback_text)

    await message.answer("✅ Спасибо за ваш отзыв!")
    await show_main_menu(message)
    await state.clear()

router = Router()

@router.message(F.text == "Вернуться в главное меню")
async def go_to_main_menu(message: types.Message, state: FSMContext):
    """
    Обрабатывает нажатие кнопки "Вернуться в главное меню".
    Очищает состояние и возвращает пользователя в главное меню.
    """
    # Очищаем состояние, если оно используется
    await state.clear()

    # Отправляем пользователю главное меню
    await show_main_menu(message)

logger = logging.getLogger(__name__)

async def subscribe_notifications(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает подписку на уведомления.
    """
    user_id = callback.from_user.id
    logger.info(f"Пользователь {user_id} подписался на уведомления.")

    # Сохраняем информацию о подписке в базу данных
    cursor.execute('''
    INSERT OR REPLACE INTO notifications (user_id, subscribed)
    VALUES (?, ?)
    ''', (user_id, True))
    conn.commit()

    await callback.message.answer("✅ Вы успешно подписались на ежедневные уведомления!")
    await state.set_state(NotificationStates.subscribed)
    await show_main_menu(callback)

async def send_daily_notifications(bot: Bot):
    """
    Отправляет ежедневные уведомления подписанным пользователям.
    """
    # Получаем всех подписанных пользователей
    cursor.execute('SELECT user_id FROM notifications WHERE subscribed = ?', (True,))
    users = cursor.fetchall()

    for user in users:
        user_id = user[0]
        try:
            await bot.send_message(user_id, "⏰ Доброе утро! Не забудьте пройти тесты сегодня!")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления пользователю {user_id}: {e}")

def register_handlers(dp):
    dp.callback_query.register(start_choosen_test, F.data.startswith("test_type:"))
    dp.callback_query.register(go_to_new_keyboard, F.data == "training_with_tasks")
    dp.callback_query.register(start_complex_test, F.data == "complex_test")
    dp.callback_query.register(show_test_history, F.data == "tests_history")
    dp.callback_query.register(show_statistics, F.data == "tests_statistics")
    dp.callback_query.register(request_delete_history, F.data == "delete_history")
    dp.callback_query.register(request_delete_statistics, F.data == "delete_statistics")
    dp.callback_query.register(confirm_delete, F.data.startswith("confirm_"))
    dp.callback_query.register(cancel_delete, F.data == "cancel_delete")
    dp.callback_query.register(request_feedback, F.data == "leave_feedback")
    dp.callback_query.register(subscribe_notifications, F.data == "subscribe_notifications")
    dp.message.register(check_test_answer, TestStates.waiting_for_answer)
    dp.message.register(process_feedback, FeedbackStates.waiting_for_feedback)