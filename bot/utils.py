import sqlite3
from datetime import datetime, timedelta
from database import DB_NAME


def format_time(seconds):
    """Форматує залишковий час у вигляді '4 години 59 хвилин 51 секунд'."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    sec = seconds % 60
    return f"{hours} годин {minutes} хвилин {sec} секунд"

def calculate_end_time(remaining_seconds, resume_time_str):
    """Обчислює орієнтовний час завершення зміни."""
    resume_time = datetime.strptime(resume_time_str, "%Y-%m-%d %H:%M:%S")
    estimated_end_time = resume_time + timedelta(seconds=remaining_seconds)
    return estimated_end_time.strftime("%H:%M:%S")

def get_remaining_time(user_id):
    """Обчислює, скільки часу залишилось до 5 або 10 годин роботи, і коли приблизно завершиться зміна."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Отримуємо початковий час активної зміни
    cursor.execute(
        "SELECT start_day, start_time FROM shifts WHERE user_id = ? AND end_time IS NULL",
        (user_id,)
    )
    result = cursor.fetchone()
    if not result:
        conn.close()
        return None  # Якщо немає активної зміни

    start_day, start_time = result
    start_datetime = datetime.strptime(f"{start_day} {start_time}", "%Y-%m-%d %H:%M:%S")

    # Підраховуємо загальну тривалість пауз
    cursor.execute(
        "SELECT SUM(pause_duration) FROM pauses WHERE shift_id = (SELECT id FROM shifts WHERE user_id = ? AND end_time IS NULL)",
        (user_id,)
    )
    pause_time = cursor.fetchone()[0] or 0  # Якщо пауз немає, то 0

    conn.close()

    # Обчислюємо фактичний робочий час
    current_time = datetime.now()
    worked_time = int((current_time - start_datetime).total_seconds()) - pause_time

    # Обчислюємо залишок до 5 і 10 годин
    target_5h = max(0, 5 * 3600 - worked_time)
    target_10h = max(0, 10 * 3600 - worked_time)

    # Розраховуємо приблизний час завершення зміни
    estimated_end_5h = (current_time + timedelta(seconds=target_5h)).strftime("%H:%M:%S") if target_5h > 0 else "Вже відпрацьовано"
    estimated_end_10h = (current_time + timedelta(seconds=target_10h)).strftime("%H:%M:%S") if target_10h > 0 else "Вже відпрацьовано"

    return target_5h, target_10h, estimated_end_5h, estimated_end_10h