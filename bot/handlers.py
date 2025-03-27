import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, timedelta
from keyboards import main_menu, active_shift_menu, paused_shift_menu, manual_add_shift_menu
from database import *
from config import DEBUG_MODE
from utils import format_time, calculate_end_time, get_remaining_time

router = Router()

class ManualShiftState(StatesGroup):
    waiting_for_manual_shift = State()

@router.message(F.text == "/start") 
async def start_command(message: Message):
    await message.answer("Вітаю! Це трекер робочого часу. Обери дію:", reply_markup=main_menu)

def register_handlers(dp):
    dp.include_router(router)

@router.message(F.text == "🔙 Назад")
async def back_button_handler(message: Message, state: FSMContext):
    user_data = await state.get_data()
    previous_menu = user_data.get("previous_menu", "main")

    if previous_menu == "main":
        await message.answer("🏠 Головне меню", reply_markup=main_menu)
    elif previous_menu == "shift":
        await message.answer("🔄 Меню зміни", reply_markup=active_shift_menu)
    
    # Оновлюємо історію, щоб при наступному "Назад" не повертатися в той самий пункт
    await state.update_data(previous_menu="main")

@router.message(F.text == "⏳ Почати зміну")
async def start_shift_handler(message: types.Message, state: FSMContext):
    """Обробник початку зміни."""
    user_id = message.from_user.id
    start_time, start_day = start_shift(user_id)
    
    if start_time:
        await state.update_data(previous_menu="main")
        await message.answer(f"✅ Зміна розпочата!\n📅 День: {start_day}\n🕒 Час: {start_time}", reply_markup=active_shift_menu)
    else:
        await message.answer("❌ Ви вже маєте активну зміну!", reply_markup=active_shift_menu)

@router.message(F.text == "⏸ Призупинити зміну")
async def pause_shift_handler(message: types.Message):
    user_id = message.from_user.id
    pause_time = pause_shift(user_id)  # Записуємо початок паузи

    if pause_time:
        dt = datetime.strptime(pause_time, "%Y-%m-%d %H:%M:%S")
        formatted_time = dt.strftime("%H:%M, %d.%m.%Y")

        await message.answer(
            f"⏸️ Зміна призупинена о {formatted_time}.",
            reply_markup=paused_shift_menu
        )
    else:
        await message.answer("⚠️ Помилка: зміна не була активною або вже на паузі.")


@router.message(F.text == "▶️ Продовжити зміну")
async def resume_shift_handler(message: types.Message):
    user_id = message.from_user.id
    result = resume_shift(user_id)  # Отримуємо тривалість паузи, залишковий час та час продовження

    if result is not None:
        pause_duration, remaining_time, resume_time_str = result
        time_text = format_time(pause_duration)
        remaining_text = format_time(remaining_time)
        estimated_end_time = calculate_end_time(remaining_time, resume_time_str)

        await message.answer(
            f"▶️ Зміна відновлена!\n"
            f"⏸ Загальний час у паузі: {time_text}.\n"
            f"🕒 Залишилося відпрацювати: {remaining_text} (орієнтовно закінчення о {estimated_end_time}).",
            reply_markup=active_shift_menu
        )
    else:
        await message.answer("⚠️ Помилка: немає активної зміни або зміна не була на паузі.")

@router.message(F.text == "⏳ Перевірити залишок часу для відпрацювання")
async def check_remaining_time_handler(message: types.Message):
    """Перевіряє залишок часу до 5 і 10 годин роботи та орієнтовний час завершення зміни."""
    user_id = message.from_user.id
    remaining_time = get_remaining_time(user_id)

    if remaining_time is None:
        await message.answer("❌ У вас немає активної зміни!", reply_markup=main_menu)
        return

    # Отримуємо статус зміни (active / paused)
    shift_status = get_shift_status(user_id)

    # Визначаємо, яке меню повертати
    reply_markup = active_shift_menu if shift_status == "active" else paused_shift_menu

    time_to_5h, time_to_10h, estimated_end_5h, estimated_end_10h = remaining_time

    def format_time(seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours} год {minutes} хв" if seconds > 0 else "⏳ Вже відпрацьовано"

    await message.answer(
        f"⏳ Час до 5 годин: {format_time(time_to_5h)} \n"
        f"🏁 Орієнтовне закінчення (5 год): {estimated_end_5h} \n\n"
        f"⏳ Час до 10 годин: {format_time(time_to_10h)} \n"
        f"🏁 Орієнтовне закінчення (10 год): {estimated_end_10h}",
        reply_markup=reply_markup
    )

@router.message(F.text == "✅ Завершити зміну")
async def end_shift_handler(message: types.Message, state: FSMContext):
    """Завершує зміну з урахуванням пауз."""
    user_id = message.from_user.id
    shift_info = end_shift(user_id)  # Отримуємо дані про зміну
    
    if not shift_info or not isinstance(shift_info, tuple) or len(shift_info) != 4:
        print(f"Помилка: очікувалося 4 значення, отримано {len(shift_info) if shift_info else 'None'} - {shift_info}")
        await message.answer("❌ У вас немає активної зміни!", reply_markup=main_menu)
        return

    start_time, end_time, total_time, pause_time = shift_info

    # Форматуємо час початку і завершення зміни
    if len(start_time) == 8:  
        start_time = datetime.now().strftime("%Y-%m-%d") + " " + start_time  # Додаємо сьогоднішню дату

    start_dt = datetime.strptime(start_time, "%d.%m.%Y о %H:%M:%S")
    end_dt = datetime.strptime(end_time, "%d.%m.%Y о %H:%M:%S")

    formatted_start = start_dt.strftime("%d.%m.%Y о %H:%M")
    formatted_end = end_dt.strftime("%d.%m.%Y о %H:%M")

    # Загальний час зміни без урахування пауз
    total_seconds = int((end_dt - start_dt).total_seconds() - pause_time)

    # Форматуємо тривалість зміни
    def format_duration(seconds):
        if seconds < 60:
            return f"{seconds} секунд"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds %= 60
            return f"{minutes} хв {seconds} сек"
        elif seconds < 86400:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds %= 60
            return f"{hours} год {minutes} хв {seconds} сек"
        else:
            days = seconds // 86400
            hours = (seconds % 86400) // 3600
            minutes = (seconds % 3600) // 60
            seconds %= 60
            return f"{days} д {hours} год {minutes} хв {seconds} сек"

    total_time_str = format_duration(total_seconds)
    pause_time_str = format_duration(pause_time)

    # Оновлюємо стан і відправляємо повідомлення
    await state.update_data(previous_menu="shift")
    await message.answer(
        f"✅ Зміна завершена!\n"
        f"🕰 Початок: {formatted_start}\n"
        f"🏁 Кінець: {formatted_end}\n"
        f"⏳ Чистий робочий час: {total_time_str}.\n"
        f"⏸ Загальний час у паузі: {pause_time_str}.",
        reply_markup=main_menu
    )

@router.message(F.text == "➕ Додати зміну вручну")
async def manual_add_shift_start(message: types.Message, state: FSMContext):
    """Запитує в користувача дату та час початку/кінця зміни"""
    if DEBUG_MODE:
        print(f"[INFO] Користувач {message.from_user.id} натиснув '➕ Додати зміну вручну'")

    await message.answer(
        "📅 Введіть дату та час початку/кінця зміни у форматі:\n"
        "**дд.мм.рр гг:хх:сс / дд.мм.рр гг:хх:сс**",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(ManualShiftState.waiting_for_manual_shift)


@router.message(ManualShiftState.waiting_for_manual_shift)
async def manual_add_shift_process(message: types.Message, state: FSMContext):
    """Обробляє введену зміну і передає в базу"""
    if DEBUG_MODE:
        print(f"[INFO] Отримано повідомлення від {message.from_user.id}: {message.text}")

    try:
        # Парсимо введені дані
        data = message.text.strip().split(" / ")
        if DEBUG_MODE:    
            print(f"[DEBUG] Розбите повідомлення: {data}")

        if len(data) != 2:
            raise ValueError("Невірний формат! Очікується два значення, розділені ' / '.")

        start_str, end_str = data

        # Конвертуємо строки в datetime
        start_dt = datetime.strptime(start_str, "%d.%m.%y %H:%M:%S")
        end_dt = datetime.strptime(end_str, "%d.%m.%y %H:%M:%S")
        if DEBUG_MODE:
            print(f"[DEBUG] Отримано дати: {start_dt} - {end_dt}")

        if start_dt >= end_dt:
            raise ValueError("Час початку має бути раніше за час завершення!")

        user_id = message.from_user.id

        # Викликаємо функцію додавання зміни в БД
        if DEBUG_MODE:
            print(f"[INFO] Додаємо зміну в БД для user_id={user_id}: {start_dt} - {end_dt}")
        shift_number = await add_manual_shift(user_id, start_dt, end_dt)

        if DEBUG_MODE:
            print(f"[INFO] Успішно додано зміну №{shift_number}")

        await message.answer(
            f"✅ Нова зміна *№{shift_number}* успішно додана!\n"
            f"📅 Початок: {start_dt.strftime('%d.%m.%y о %H:%M:%S')}\n"
            f"🏁 Закінчення: {end_dt.strftime('%d.%m.%y о %H:%M:%S')}",
            reply_markup=manual_add_shift_menu
        )

    except ValueError as e:
        if DEBUG_MODE:
            print(f"[WARNING] Користувач ввів неправильні дані: {e}")
        await message.answer(f"❌ Помилка: {e}\nСпробуйте ще раз!")

    except Exception as e:
        if DEBUG_MODE:
            logging.exception("[ERROR] Виникла невідома помилка при додаванні зміни!")
        await message.answer("⚠️ Сталася невідома помилка! Спробуйте ще раз.")

    await state.clear()

@router.message(F.text == "📊 Переглянути зміни")
async def shifts_handler(message: types.Message, state: FSMContext):
    """Команда для перегляду змін з нумерацією в межах тижня."""
    user_id = message.from_user.id
    shifts = get_shifts(user_id)

    if not shifts:
        await message.answer("ℹ️ У вас ще немає записаних змін.")
        return

    
    shifts_by_week = {}
    
    for start, day, end in shifts:
        
        start_dt = datetime.strptime(day, "%Y-%m-%d")
        week_start = start_dt - timedelta(days=start_dt.weekday())  
    
        if week_start not in shifts_by_week:
            shifts_by_week[week_start] = []
        shifts_by_week[week_start].append((start, day, end))

    text = "📋 *Ваші зміни по тижнях:*\n\n"

    for week_start, week_shifts in sorted(shifts_by_week.items(), reverse=True):
        text += f"📅 *Тиждень: {week_start.strftime('%d.%m.%y')} - {(week_start + timedelta(days=6)).strftime('%d.%m.%y')}*\n"

        for index, (start, day, end) in enumerate(week_shifts, start=1):
            day_name = datetime.strptime(day, "%Y-%m-%d").strftime("%A")  
            text += f"  🔹 {day_name} ({day}) — Зміна #{index}: {start} - {end or '❌ не завершена'}\n"

        text += "\n"

    await state.update_data(previous_menu="main")
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "🗑 Видалити зміну")
async def delete_shift_handler(message: types.Message):
    """Видалення останньої зміни."""
    user_id = message.from_user.id
    result = delete_last_shift(user_id)
    
    if result:
        await message.answer("✅ Останню зміну успішно видалено.")
    else:
        await message.answer("❌ У вас немає змін для видалення.")