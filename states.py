from aiogram.fsm.state import State, StatesGroup

# Состояния для регистрации
class Registration(StatesGroup):
    waiting_for_name = State()

# Состояния для тестов
class TestStates(StatesGroup):
    waiting_for_answer = State()