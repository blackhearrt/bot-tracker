from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⏳ Почати зміну")],
        [KeyboardButton(text="✅ Завершити зміну")],
        [KeyboardButton(text="📊 Переглянути зміни")]
    ],
    resize_keyboard=True
)