from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


# Головне меню перед початком зміни
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⏳ Почати зміну")],
        [KeyboardButton(text="📊 Переглянути зміни"), KeyboardButton(text="🗑 Видалити зміну")]
    ],
    resize_keyboard=True
)

# Меню під час активної зміни
active_shift_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⏸ Призупинити зміну"), KeyboardButton(text="✅ Завершити зміну")], [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

# Меню, коли зміна призупинена
paused_shift_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="▶️ Продовжити зміну")], [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)