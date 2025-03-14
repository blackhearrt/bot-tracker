import logging
import asyncio
from aiogram import Bot, Dispatcher
import os
from database import init_db
from dotenv import load_dotenv
from handlers import router

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(router)

async def main():
    logging.basicConfig(level=logging.INFO)
    
    init_db()
    
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())