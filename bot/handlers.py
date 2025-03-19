from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, timedelta
from keyboards import main_menu, active_shift_menu, paused_shift_menu
from database import start_shift, end_shift, get_shifts, delete_last_shift, pause_shift, resume_shift

router = Router()

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
    pause_time = pause_shift(user_id)  # Отримуємо поточний час

    if pause_time:
        dt = datetime.strptime(pause_time, "%Y-%m-%d %H:%M:%S")  # Перетворюємо рядок у datetime
        formatted_time = dt.strftime("%H:%M, %d.%m.%Y")  # Форматування в "час, дата"

        await message.answer(
            f"⏸️ Зміна призупинена о {formatted_time}.",
            reply_markup=paused_shift_menu
        )
    else:
        await message.answer("⚠️ Помилка: зміна не була активною або вже на паузі.")

@router.message(F.text == "▶️ Продовжити зміну")
async def resume_shift_handler(message: types.Message):
    user_id = message.from_user.id
    total_pause_time = resume_shift(user_id)  # Отримуємо тривалість паузи

    if total_pause_time:
        h, m, s = map(int, total_pause_time.split(":"))
        total_pause_seconds = h * 3600 + m * 60 + s  # Переводимо в секунди

        if total_pause_seconds >= 60 and total_pause_seconds < 3600:
            time_text = f"{total_pause_seconds // 60} хвилин {total_pause_seconds % 60} секунд"
        elif total_pause_seconds >= 3600:
            time_text = f"{total_pause_seconds // 3600} годин {total_pause_seconds % 3600 // 60} хвилин {total_pause_seconds % 60} секунд"
        else:
            time_text = f"{total_pause_seconds} секунд"

        await message.answer(
            f"▶️ Зміна відновлена! Загальний час паузи: {time_text}.",
            reply_markup=active_shift_menu
        )
    else:
        await message.answer("⚠️ Помилка: немає активної зміни або зміна не була на паузі.")



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
    if len(start_time) == 8:  # Якщо тільки час (наприклад, '14:49:44')
        start_time = datetime.now().strftime("%Y-%m-%d") + " " + start_time  # Додаємо сьогоднішню дату

    start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(end_time, "%d-%m-%Y %H:%M:%S")

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