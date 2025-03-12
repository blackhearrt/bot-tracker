import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")  # Токен бота з .env файлу
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Головне меню
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("🟢 Почати зміну"))
main_menu.add(KeyboardButton("📋 Відпрацьовані зміни"))

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    await message.answer("Вітаю! Це бот для трекінгу робочого часу. Виберіть дію:", reply_markup=main_menu)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)