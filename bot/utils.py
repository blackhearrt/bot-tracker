from datetime import datetime, timedelta

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