from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="Комплексный тест", callback_data="complex_test")],
        [InlineKeyboardButton(text="Тренировка с заданиями по выбору", callback_data="training_with_tasks")],
        [InlineKeyboardButton(text="История прохождения тестов", callback_data="tests_history")],
        [InlineKeyboardButton(text="Посмотреть статистику", callback_data="tests_statistics")],
        [InlineKeyboardButton(text="Удалить историю", callback_data="delete_history")],
        [InlineKeyboardButton(text="Удалить статистику", callback_data="delete_statistics")],
        [InlineKeyboardButton(text="Оставить отзыв", callback_data="leave_feedback")],
        [InlineKeyboardButton(text="Подписаться на уведомления", callback_data="subscribe_notifications")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_choose_test_keyboard():
    keyboard = [
        [InlineKeyboardButton(text="Посчитайте количество заданного слова в тексте", callback_data="test_type:word_count")],
        [InlineKeyboardButton(text="Посчитайте количество заданной буквы в тексте", callback_data="test_type:letter_count")],
        [InlineKeyboardButton(text="Найти лишнее слово в списке", callback_data="test_type:extra_word")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirmation_keyboard(action: str):
    """
    Создаёт клавиатуру для подтверждения удаления.
    :param action: Действие (delete_history или delete_statistics)
    """
    keyboard = [
        [InlineKeyboardButton(text="Да", callback_data=f"confirm_{action}")],
        [InlineKeyboardButton(text="Нет", callback_data="cancel_delete")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_return_to_main_menu_keyboard():
    """
    Создаёт Reply-клавиатуру с кнопкой "Вернуться в главное меню".
    """
    keyboard = [
        [KeyboardButton(text="Вернуться в главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True)
