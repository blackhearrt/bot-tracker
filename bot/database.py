import sqlite3
from datetime import datetime

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
        )
    """)

    conn.commit()
    conn.close()
    print("База даних ініціалізована!")


def start_shift(user_id):
    """Записує початок зміни з днем тижня."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    now = datetime.now()
    start_time = datetime.now().strftime("%H:%M:%S")
    start_day = datetime.now().strftime("%Y-%m-%d") 

    cursor.execute("INSERT INTO shifts (user_id, start_time, start_day) VALUES (?, ?, ?)", 
               (user_id, start_time, start_day))

    conn.commit()
    conn.close()
    return start_time, start_day

def pause_shift(user_id):
    """Призупиняє зміну, зберігаючи час паузи."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Перевіряємо, чи є активна зміна
    cursor.execute("SELECT id, pause_time FROM shifts WHERE user_id = ? AND end_time IS NULL", (user_id,))
    shift = cursor.fetchone()

    if shift:
        shift_id, pause_time = shift

        # Якщо пауза вже є, повертаємо помилку
        if pause_time is not None:
            conn.close()
            return None

        # Записуємо час початку паузи
        pause_time = int(datetime.now())
        cursor.execute("UPDATE shifts SET pause_time = ? WHERE id = ?", (pause_time, shift_id))
        conn.commit()
        conn.close()
        return pause_time
    else:
        conn.close()
        return None
    
def resume_shift(user_id):
    """Продовжує зміну, обчислюючи загальний час паузи."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Перевіряємо, чи є зміна на паузі
    cursor.execute("SELECT id, pause_time FROM shifts WHERE user_id = ? AND end_time IS NULL", (user_id,))
    shift = cursor.fetchone()

    if shift:
        shift_id, pause_time = shift

        # Якщо немає паузи – повертаємо помилку
        if pause_time is None:
            conn.close()
            return None

        # Обчислюємо тривалість паузи
        pause_duration = int(datetime.now()) - pause_time

        # Додаємо до загального часу роботи
        cursor.execute("UPDATE shifts SET pause_time = NULL WHERE id = ?", (shift_id,))
        conn.commit()
        conn.close()
        return pause_duration
    else:
        conn.close()
        return None

def end_shift(user_id):
    """Фіксуємо завершення останньої зміни."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    now = datetime.now()
    end_time = now.strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE shifts 
        SET end_time = ?
        WHERE user_id = ? AND end_time IS NULL
    """, (end_time, user_id))

    conn.commit()
    conn.close()
    return end_time 
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