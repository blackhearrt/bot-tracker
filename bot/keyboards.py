from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


btn_start_shift = KeyboardButton(text="🟢 Почати зміну")
btn_worked_shifts = KeyboardButton(text="📊 Відпрацьовані зміни")


main_menu = ReplyKeyboardMarkup(
    keyboard=[[btn_start_shift], [btn_worked_shifts]],
    resize_keyboard=True
)
