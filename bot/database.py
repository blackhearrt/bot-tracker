import sqlite3
import os
from datetime import datetime, timedelta, date

DB_NAME = "tracker.db"

def init_db():
    """Ініціалізація бази даних: створення таблиці, якщо її немає."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            start_day TEXT NOT NULL,
            end_time TEXT
            pause_time TEXT
            total_time TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pauses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            shift_id INTEGER NOT NULL,
            shift_start TEXT,
            pause_start TEXT NOT NULL,
            pause_end TEXT,
            pause_duration INTEGER,
            FOREIGN KEY (shift_id) REFERENCES shifts (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    print("База даних ініціалізована!")

if not os.path.exists(DB_NAME):
    print("⚠️ Файл БД відсутній! Бот створить новий порожній файл.")
else:
    print("✅ Файл БД знайдено.")

if not os.path.exists("tracker.db"):
    print("⚠️ Файл БД відсутній! Бот створить новий порожній файл.")
else:
    print("✅ Файл БД знайдено.")

def check_columns():
    conn = sqlite3.connect(DB_NAME)  
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(shifts);")
    columns = cursor.fetchall()
    conn.close()
    return columns

print("Таблиця shifts містить такі стовпці:")
for column in check_columns():
    print(column)

def start_shift(user_id):
    """Записує початок зміни з днем тижня."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    now = datetime.now()
    start_time = now.strftime("%H:%M:%S")
    start_day = now.strftime("%Y-%m-%d") 

    cursor.execute("INSERT INTO shifts (user_id, start_time, start_day) VALUES (?, ?, ?)", 
                   (user_id, start_time, start_day))

    conn.commit()
    conn.close()
    return start_time, start_day

def pause_shift(user_id):
    """Призупиняє зміну, додаючи запис про початок паузи в таблицю pauses."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Перевіряємо, чи є активна зміна
    cursor.execute("SELECT id FROM shifts WHERE user_id = ? AND end_time IS NULL", (user_id,))
    shift = cursor.fetchone()

    if not shift:
        conn.close()
        return None  # Немає активної зміни

    shift_id = shift[0]

    # Перевіряємо, чи вже є незавершена пауза
    cursor.execute("SELECT id FROM pauses WHERE shift_id = ? AND pause_end IS NULL", (shift_id,))
    existing_pause = cursor.fetchone()

    if existing_pause:
        conn.close()
        return None  # Уже є активна пауза

    # Записуємо початок паузи
    pause_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO pauses (shift_id, pause_start) VALUES (?, ?)", (shift_id, pause_start))
    
    conn.commit()
    conn.close()

    return pause_start


def resume_shift(user_id):
    """Продовжує зміну, додаючи час завершення паузи та підраховуючи її тривалість."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Отримуємо ID зміни
    cursor.execute("SELECT id, start_time, start_day FROM shifts WHERE user_id = ? AND end_time IS NULL", (user_id,))
    shift = cursor.fetchone()

    if not shift:
        conn.close()
        return None  # Немає активної зміни

    shift_id, start_time, start_day = shift

    # Отримуємо останню активну паузу
    cursor.execute("SELECT id, pause_start FROM pauses WHERE shift_id = ? AND pause_end IS NULL", (shift_id,))
    pause = cursor.fetchone()

    if not pause:
        conn.close()
        return None  # Немає активної паузи

    pause_id, pause_start = pause

    # Підраховуємо тривалість паузи
    pause_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pause_start_dt = datetime.strptime(pause_start, "%Y-%m-%d %H:%M:%S")
    pause_end_dt = datetime.strptime(pause_end, "%Y-%m-%d %H:%M:%S")
    pause_duration = int((pause_end_dt - pause_start_dt).total_seconds())

    # Оновлюємо запис у pauses
    cursor.execute("UPDATE pauses SET pause_end = ?, pause_duration = ? WHERE id = ?",
                   (pause_end, pause_duration, pause_id))

    # Отримуємо всі паузи цієї зміни
    cursor.execute("SELECT SUM(pause_duration) FROM pauses WHERE shift_id = ?", (shift_id,))
    total_pause_time = cursor.fetchone()[0] or 0  # Якщо пауз не було, то 0

    # Обчислюємо загальний час роботи без урахування пауз
    now = datetime.now()
    start_datetime_str = f"{start_day} {start_time}"
    start_time_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S")
    
    total_work_time = int((now - start_time_dt).total_seconds()) - total_pause_time

    # Обчислюємо, скільки залишилося до 5 годин (18000 секунд)
    remaining_time = max(18000 - total_work_time, 0)

    conn.commit()
    conn.close()

    return pause_duration, remaining_time, pause_end  # Повертаємо час закінчення паузи

def get_shift_status(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Шукаємо активну зміну
    cursor.execute("SELECT id FROM shifts WHERE user_id = ? AND end_time IS NULL", (user_id,))
    shift = cursor.fetchone()

    if not shift:
        conn.close()
        return None  # Зміни немає

    shift_id = shift[0]

    # Перевіряємо, чи є незакрита пауза
    cursor.execute("SELECT id FROM pauses WHERE shift_id = ? AND pause_end IS NULL", (shift_id,))
    pause = cursor.fetchone()

    conn.close()

    return "paused" if pause else "active"

def end_shift(user_id):
    """Завершує зміну та рахує загальний час без пауз."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Отримуємо shift_id, start_day, start_time для активної зміни
    cursor.execute(
        "SELECT id, start_day, start_time FROM shifts WHERE user_id = ? AND end_time IS NULL",
        (user_id,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return None

    shift_id, start_day, start_time = result  # Додаємо shift_id
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Об'єднуємо дату та час у правильному форматі
    start_datetime_str = f"{start_day} {start_time}"
    start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    # Підраховуємо загальний час зміни
    total_time = int((end_dt - start_dt).total_seconds())

    # Підраховуємо загальний час пауз із таблиці `pauses`
    cursor.execute(
        "SELECT SUM(pause_duration) FROM pauses WHERE shift_id = ?",
        (shift_id,)
    )
    pause_time = cursor.fetchone()[0]
    pause_time = int(pause_time) if pause_time else 0  # Якщо пауз не було, то 0

    # Закриваємо зміну
    cursor.execute(
        "UPDATE shifts SET end_time = ?, total_time = ?, pause_time = ? WHERE id = ?",
        (end_time, total_time, pause_time, shift_id)
    )

    conn.commit()
    conn.close()

    # Форматуємо дату у вигляді "дд.мм.рррр о год:хв:сек"
    start_dt_formatted = start_dt.strftime("%d.%m.%Y о %H:%M:%S")
    end_dt_formatted = end_dt.strftime("%d.%m.%Y о %H:%M:%S")

    return start_dt_formatted, end_dt_formatted, total_time, pause_time

def get_shifts(user_id):
    """Отримуємо список змін користувача."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT start_time, start_day, end_time FROM shifts 
        WHERE user_id = ? ORDER BY start_time DESC
    """, (user_id,))
    
    shifts = cursor.fetchall()
    conn.close()
    return shifts

def count_shifts(user_id):
    """Підраховуємо кількість змін користувача."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM shifts WHERE user_id = ?", (user_id,))
    count = cursor.fetchone()[0]

    conn.close()
    return count

def delete_last_shift(user_id):
    """Видаляє останню зміну користувача."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM shifts WHERE user_id = ? ORDER BY start_time DESC LIMIT 1", (user_id,))
    last_shift = cursor.fetchone()
    
    if last_shift:
        cursor.execute("DELETE FROM shifts WHERE id = ?", (last_shift[0],))
        conn.commit()
        conn.close()
        return True
    else:
        conn.close()
        return False