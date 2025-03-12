from aiogram import Router, F
from aiogram.types import Message
from keyboards import main_menu

router = Router()

@router.message(F.text == "/start") 
async def start_command(message: Message):
    await message.answer("Вітаю! Це трекер робочого часу. Обери дію:", reply_markup=main_menu)

def register_handlers(dp):
    dp.include_router(router)

