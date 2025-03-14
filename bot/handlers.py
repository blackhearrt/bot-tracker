from aiogram import Router, F, types
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime, timedelta
from keyboards import main_menu
from database import start_shift, end_shift, get_shifts

router = Router()

@router.message(F.text == "/start") 
async def start_command(message: Message):
    await message.answer("Вітаю! Це трекер робочого часу. Обери дію:", reply_markup=main_menu)

def register_handlers(dp):
    dp.include_router(router)

@router.message(F.text == "⏳ Почати зміну")
async def start_shift_handler(message: types.Message):
    """Команда для початку зміни."""
    user_id = message.from_user.id
    start_time, start_day = start_shift(user_id)
    await message.answer(f"✅ Зміна розпочата!\n📅 День: {start_day}\n🕒 Час: {start_time}")

@router.message(F.text == "✅ Завершити зміну")
async def end_shift_handler(message: types.Message):
    """Команда для завершення зміни."""
    user_id = message.from_user.id
    end_time = end_shift(user_id)
    if end_time:
        await message.answer(f"✅ Зміна завершена!\n🕒 Час: {end_time}")
    else:
        await message.answer("❌ Ви не починали зміну!")

@router.message(F.text == "📊 Переглянути зміни")
async def shifts_handler(message: types.Message):
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

    await message.answer(text, parse_mode="Markdown")
