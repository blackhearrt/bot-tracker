import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.utils import executor
import os
from dotenv import load_dotenv
from bot.handlers import register_handlers

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

register_handlers(dp)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    executor.start_polling(dp, skip_updates=True)