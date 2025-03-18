import sqlite3
from datetime import datetime, timedelta

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
        pause_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("UPDATE shifts SET pause_time = ? WHERE id = ?", (pause_time, shift_id))
        conn.commit()
        conn.close()
        return pause_time
    else:
        conn.close()
        return None
    
def resume_shift(user_id):
    """Продовжує зміну, обчислюючи загальний час паузи та коригуючи початок зміни."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Отримуємо ID зміни, час початку, день початку та час паузи
    cursor.execute("SELECT id, start_time, start_day, pause_time FROM shifts WHERE user_id = ? AND end_time IS NULL", (user_id,))
    shift = cursor.fetchone()

    if shift:
        shift_id, start_time, start_day, pause_time = shift

        # Якщо паузи немає – повертаємо None
        if pause_time is None:
            conn.close()
            return None

        # **Формуємо правильний start_time**
        if len(start_time) == 8:  # Формат HH:MM:SS, треба додати дату
            start_time = f"{start_day} {start_time}"

        # Конвертуємо строки в datetime
        start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        pause_time = datetime.strptime(pause_time, "%Y-%m-%d %H:%M:%S")

        # Обчислюємо тривалість паузи
        pause_duration = datetime.now() - pause_time

        # **Коригуємо початковий час зміни**
        corrected_start_time = start_time + pause_duration

        # Оновлюємо базу: прибираємо паузу, оновлюємо початок зміни
        cursor.execute("UPDATE shifts SET pause_time = NULL, start_time = ? WHERE id = ?", 
                       (corrected_start_time.strftime("%H:%M:%S"), shift_id))
        conn.commit()
        conn.close()
        
        return str(pause_duration).split(".")[0]
    else:
        conn.close()
        return None

def end_shift(user_id):
    """Завершує зміну та рахує загальний час без пауз."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Отримуємо дату та час початку зміни
    cursor.execute(
        "SELECT start_day, start_time FROM shifts WHERE user_id = ? AND end_time IS NULL",
        (user_id,)
    )
    result = cursor.fetchone()

    if not result:
        conn.close()
        return None

    start_day, start_time = result  # Розпаковуємо результат (дата, час)
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Об'єднуємо дату та час у правильному форматі
    start_datetime_str = f"{start_day} {start_time}"
    start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")

    # Підраховуємо загальний час зміни
    total_time = int((end_dt - start_dt).total_seconds())

    # Отримуємо загальний час пауз
    cursor.execute(
        "SELECT SUM(duration) FROM pauses WHERE user_id = ? AND shift_start = ?",
        (user_id, start_datetime_str)
    )
    pause_result = cursor.fetchone()
    pause_time = pause_result[0] if pause_result[0] else 0  # Якщо пауз не було, повертаємо 0

    # Закриваємо зміну
    cursor.execute(
        "UPDATE shifts SET end_time = ?, total_time = ? WHERE user_id = ? AND start_day = ? AND start_time = ?",
        (end_time, total_time, user_id, start_day, start_time)
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