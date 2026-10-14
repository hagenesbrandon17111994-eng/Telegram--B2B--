import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
import random
from datetime import datetime, timedelta

# 1. Настройка базы данных и мок-данных
DB_FILE = "b2b_leads.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            manager TEXT,
            status TEXT,
            amount INTEGER
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM leads")
    if cursor.fetchone()[0] == 0:
        managers = ['Иванов', 'Петров', 'Смирнова']
        statuses = ['Новый', 'В работе', 'Успешно', 'Отказ']
        start_date = datetime.now() - timedelta(days=30)
        for _ in range(200):
            l_date = start_date + timedelta(days=random.randint(0, 30))
            cursor.execute('INSERT INTO leads (date, manager, status, amount) VALUES (?, ?, ?, ?)', 
                  (l_date.strftime('%Y-%m-%d'), random.choice(managers), 
                   random.choices(statuses, weights=[10, 30, 40, 20])[0], random.randint(50, 300)*1000))
        conn.commit()
    conn.close()

def generate_report():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM leads", conn)
    conn.close()

    df_success = df[df['status'] == 'Успешно']
    sales_by_manager = df_success.groupby('manager')['amount'].sum().sort_values()

    plt.figure(figsize=(8, 6))
    sales_by_manager.plot(kind='barh', color='#4CAF50')
    plt.title('Объем успешных B2B-сделок по менеджерам', fontsize=14)
    plt.xlabel('Сумма (руб)', fontsize=12)
    plt.ylabel('Менеджер', fontsize=12)
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    report_path = "sales_report.png"
    plt.savefig(report_path, dpi=300)
    plt.close()
    
    total = len(df)
    success = len(df_success)
    return report_path, f"📊 Отчет сформирован.\nВсего заявок: {total}\nУспешных: {success}\nКонверсия: {(success/total)*100 if total>0 else 0:.1f}%"

BOT_TOKEN = "ВАШ_ТОКЕН_ЗДЕСЬ"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Нажми /report, чтобы получить аналитику по сделкам.")

@dp.message(Command("report"))
async def cmd_report(message: types.Message):
    await message.answer("⏳ Генерирую график...")
    photo_path, text_stats = generate_report()
    await bot.send_photo(chat_id=message.chat.id, photo=FSInputFile(photo_path), caption=text_stats)

async def main():
    init_db()
    print("Бот запущен! Перейдите в Telegram и напишите ему /start")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
