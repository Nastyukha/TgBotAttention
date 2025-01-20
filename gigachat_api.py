from config import GigaChatKey
from langchain_gigachat.chat_models import GigaChat
from langchain_core.messages import HumanMessage, SystemMessage

# Инициализация GigaChat
LLM = GigaChat(
    credentials=GigaChatKey,
    scope="GIGACHAT_API_PERS",
    model="GigaChat",
    verify_ssl_certs=False,
    streaming=False,
)

# Системное сообщение для генерации тестов
system_message = SystemMessage(
    content="Вы — помощник, который генерирует тесты на внимание по заданным темам."
)

# Функция генерации тестов
def generate_attention_test(test_type: str) -> tuple[str, str]:
    messages = [system_message]

    if test_type == "посчитать слова":
        # Генерация текста и задания для подсчёта количества слов
        messages.append(HumanMessage(
            content="Сгенерируй текст минимум из 30 слов. Выбери случайное слово из текста и создай задание: 'Посчитайте, сколько раз встречается слово **X** в тексте.' В ответе сначала напиши задание, а потом текст."
        ))
    elif test_type == "посчитать буквы":
        # Генерация текста и задания для подсчёта количества букв
        messages.append(HumanMessage(
            content="Сгенерируй текст максимум из 30 слов. Выбери случайную букву из текста и создай задание: 'Посчитайте, сколько раз встречается буква **X** в тексте.' В ответе сначала напиши задание, а потом текст."
        ))
    elif test_type == "найти лишнее слово":
        # Генерация текста и задания для выбора лишнего
        messages.append(HumanMessage(
            content="Сгенерируй набор слов, одно из которых будет лишним. Создай задание:'Найди лишнее слово'. В ответе сначала напиши задание, а потом пронумерованный список слов."
        ))
    else:
        raise ValueError("Неизвестный тип теста")

    # Генерация задания
    response = LLM.invoke(messages)
    question = response.content

    # Генерация правильного ответа
    correct_answer_messages = [system_message]
    correct_answer_messages.append(HumanMessage(
        content=f"Для задания: '{question}' укажи правильный ответ. В сообщении отправь только подходящую цифру"
    ))
    correct_answer_response = LLM.invoke(correct_answer_messages)
    correct_answer = correct_answer_response.content

    return question, correct_answer