import logging
import asyncio
from aiogram import Bot, Dispatcher
import os
from database import create_db_pool, create_tables
from dotenv import load_dotenv
from handlers import register_handlers

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()


async def main():
    pool = await create_db_pool() 
    await create_tables(pool)  
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    register_handlers(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())