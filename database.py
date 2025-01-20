import sqlite3

# Подключение к базе данных SQLite
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы пользователей
def init_db():
    # Создание таблицы users
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        name TEXT
    )
    ''')

    # Создание таблицы test_history
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        test_type TEXT,
        result TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')

    # Создание таблицы test_statistics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS test_statistics (
        user_id INTEGER PRIMARY KEY,
        total_tests INTEGER DEFAULT 0,
        correct_answers INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')

    # Создание таблицы feedback
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        user_name TEXT,  -- Новый столбец для имени пользователя
        feedback_text TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')

    # Создание таблицы notifications
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        user_id INTEGER PRIMARY KEY,
        subscribed BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    conn.commit()