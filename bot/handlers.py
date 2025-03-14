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
        await message.answer("🏠 Головне меню", reply_markup=main_menu())
    elif previous_menu == "shift":
        await message.answer("🔄 Меню зміни", reply_markup=active_shift_menu())
    
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
    """Призупиняє зміну."""
    user_id = message.from_user.id
    pause_time = pause_shift(user_id)
    
    if pause_time:
        await message.answer(f"⏸ Зміна призупинена о {pause_time}.", reply_markup=paused_shift_menu)
    else:
        await message.answer("❌ У вас немає активної зміни або зміна вже призупинена!")

@router.message(F.text == "▶️ Продовжити зміну")
async def resume_shift_handler(message: types.Message):
    """Продовжує зміну після паузи."""
    user_id = message.from_user.id
    total_pause_time = resume_shift(user_id)
    
    if total_pause_time is not None:
        await message.answer(f"▶️ Зміна відновлена! Загальний час пауз: {total_pause_time // 60} хвилин.", reply_markup=active_shift_menu)
    else:
        await message.answer("❌ Ви не призупиняли зміну або вона вже триває!")



@router.message(F.text == "✅ Завершити зміну")
async def end_shift_handler(message: types.Message, state: FSMContext):
    """Завершує зміну."""
    user_id = message.from_user.id
    shift_info = end_shift(user_id)
    
    if shift_info:
        start_time, end_time, total_time = shift_info
        await state.update_data(previous_menu="shift")
        await message.answer(
            f"✅ Зміна завершена!\n"
            f"🕰 Початок: {start_time}\n"
            f"🏁 Кінець: {end_time}\n"
            f"⏳ Загальна тривалість: {total_time // 60} хвилин.",
            reply_markup=main_menu
        )
    else:
        await message.answer("❌ У вас немає активної зміни!", reply_markup=main_menu)

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