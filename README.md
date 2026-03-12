# Telegram Time Tracker Bot

Telegram bot for tracking work sessions and recording working hours.

The bot allows users to start and pause work sessions, finish shifts and review recorded work statistics.

The project demonstrates building a **stateful Telegram bot with persistent storage** using Python.

---

## Project Goal

The purpose of this project is to create a simple but reliable system for tracking work sessions through Telegram.

Typical use cases:

• freelancers tracking working hours  
• testers logging work sessions  
• developers monitoring time spent on tasks  

The project also serves as a practical example of building **Telegram automation tools with Python**.

---

## Features

• start a work session  
• pause and resume sessions  
• finish shifts and calculate total time worked  
• view recorded shifts  
• delete incorrect entries  
• check remaining work time during a shift  

The bot stores all session data locally using a lightweight database.

---

## Tech Stack

Python

Libraries and tools:

- aiogram 3
- asyncio
- SQLite3

Main concepts used in the project:

• asynchronous Telegram bot architecture  
• session state management  
• database persistence  
• command handlers and routing  

---

## How It Works

1. User starts a work session through the Telegram bot.
2. Session state is stored in the database.
3. User can pause or resume the session.
4. When the shift ends, total worked time is calculated and saved.
5. Users can view their work history or delete incorrect records.

---

## Installation
<details>
  
Clone the repository:  
```bash
git clone https://github.com/blackhearrt/time-tracker-bot
cd time-tracker-bot
```  
Install dependencies:
```bash
pip install -r requirements.txt
```  
Create a .env file in the project root and add your Telegram bot token:
```bash
BOT_TOKEN=your_token_here
```  
Run the bot:
```bash
python main.py
```
</details>  

---

## Future Improvements

Planned features:

• automatic reminders to finish shifts  
• daily / weekly work reports  
• export of statistics  
• Google Sheets integration  
• improved analytics of work sessions  

---

## Author

Serhii Mamonov

Python developer transitioning into **Data Analytics and automation**.

Background in biotechnology and analytical workflows.

