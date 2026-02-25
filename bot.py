import asyncio
import sqlite3
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage


ADMIN_ID = 911966345  # Твой Telegram ID (число)
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ Токен не найден!")
    exit(1)
# ---------------------------------------------------------

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- База данных SQLite ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            workplace TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("✅ База данных готова")

init_db()

# --- Состояния для FSM ---
class Form(StatesGroup):
    name = State()
    workplace = State()
    problem = State()

# --- Клавиатуры (кнопки) ---
def get_workplace_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Офис1"), KeyboardButton(text="Офис2")],
            [KeyboardButton(text="Ресепшен"), KeyboardButton(text="Менеджеры")],
            [KeyboardButton(text="Касса"), KeyboardButton(text="РОП,РКС,Приемка")],
            [KeyboardButton(text="Логистика"), KeyboardButton(text="Салон б/у")],
            [KeyboardButton(text="Сервис"), KeyboardButton(text="Склад")]

        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите рабочее место"
    )
    return keyboard

def get_problem_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1С"), KeyboardButton(text="Принтер")],
            [KeyboardButton(text="Сильвер"), KeyboardButton(text="ВПН")],
            [KeyboardButton(text="Проблемы с ПК"), KeyboardButton(text="Картридж")],
            [KeyboardButton(text="Камеры"), KeyboardButton(text="ПАМАГИТИ")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите проблему"
    )
    return keyboard

# --- Команда /start ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Проверяем, есть ли пользователь в базе
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, workplace FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user and user[0] and user[1]:
        # Если пользователь уже зарегистрирован
        await state.update_data(name=user[0], workplace=user[1])
        await state.set_state(Form.problem)
        await message.answer(
            f"👋 С возвращением, {user[0]}!",
            reply_markup=ReplyKeyboardRemove()
        )
        await message.answer(
            "Выберите проблему:",
            reply_markup=get_problem_keyboard()
        )
    else:
        # Новый пользователь
        await state.set_state(Form.name)
        await message.answer(
            "👋 Привет! Я бот для вызова сисадмина.\n"
            "Давайте познакомимся.\n\n"
            "Как вас зовут?"
        )

# --- Ввод имени ---
@dp.message(Form.name)
async def process_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 2 or len(name) > 50:
        await message.answer("Имя должно быть от 2 до 50 символов. Попробуйте еще раз:")
        return
    
    await state.update_data(name=name)
    await state.set_state(Form.workplace)
    await message.answer(
        "📍 Выберите ваше рабочее место:",
        reply_markup=get_workplace_keyboard()
    )

# --- Ввод рабочего места ---
@dp.message(Form.workplace)
async def process_workplace(message: types.Message, state: FSMContext):
    workplace = message.text
    valid_places = ["Офис1", "Офис2", "Ресепшен", "Менеджеры", "Касса", "РОП,РКС,Приемка", "Логистика", "Салон б/у", "Сервис", "Склад"]
    
    if workplace not in valid_places:
        await message.answer(
            "Пожалуйста, выберите место из списка, используя кнопки:",
            reply_markup=get_workplace_keyboard()
        )
        return
    
    await state.update_data(workplace=workplace)
    data = await state.get_data()
    
    # Сохраняем в базу данных
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (user_id, name, workplace) VALUES (?, ?, ?)",
        (message.from_user.id, data['name'], workplace)
    )
    conn.commit()
    conn.close()
    
    await state.set_state(Form.problem)
    await message.answer(
        f"✅ Отлично, {data['name']}!",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer(
        "Выберите проблему:",
        reply_markup=get_problem_keyboard()
    )

# --- Выбор проблемы и отправка заявки ---
@dp.message(Form.problem)
async def process_problem(message: types.Message, state: FSMContext):
    problem = message.text
    valid_problems = ["1С", "Принтер", "Сильвер", "ВПН", "Проблемы с ПК", "Картридж", "Камеры", "ПАМАГИТИ"]
    
    if problem not in valid_problems:
        await message.answer(
            "Пожалуйста, выберите проблему из списка, используя кнопки:",
            reply_markup=get_problem_keyboard()
        )
        return
    
    data = await state.get_data()
    
    # Отправляем заявку администратору
    try:
        await bot.send_message(
            ADMIN_ID,
            f"🚨 **Новая заявка!**\n\n"
            f"👤 **Имя:** {data['name']}\n"
            f"📍 **Место:** {data['workplace']}\n"
            f"❓ **Проблема:** {problem}\n"
            f"🆔 **ID:** {message.from_user.id}",
            parse_mode="Markdown"
        )
        print(f"✅ Заявка отправлена админу от {data['name']}")
    except Exception as e:
        print(f"❌ Ошибка отправки админу: {e}")
    
    # Подтверждение пользователю
    await message.answer(
        "✅ **Заявка принята!**\n\n"
        "Сисадмин уже получил уведомление.\n"
        "Если хотите создать новую заявку, просто отправьте /start",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    
    await state.clear()

# --- Команда /cancel ---
@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Действие отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    await message.answer("Чтобы начать заново, нажмите /start")

# --- Команда для просмотра базы (только для админа) ---
@dp.message(Command("db"))
async def show_db(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав для этой команды")
        return
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    
    if users:
        text = "📊 **База данных сотрудников:**\n\n"
        for user in users:
            text += f"🆔 ID: {user[0]}\n👤 Имя: {user[1]}\n📍 Место: {user[2]}\n{'-'*20}\n"
    else:
        text = "📭 База данных пуста"
    
    await message.answer(text, parse_mode="Markdown")

# --- УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК (для удаленных чатов) ---
@dp.message()
async def handle_any_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    
    # Получаем текущее состояние пользователя
    current_state = await state.get_state()
    
    # Проверяем, есть ли пользователь в базе
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, workplace FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    # Если пользователя НЕТ в базе
    if not user or not user[0] or not user[1]:
        await state.clear()
        await state.set_state(Form.name)
        await message.answer(
            "👋 Привет! Я бот для вызова сисадмина.\n"
            "Давайте познакомимся.\n\n"
            "Как вас зовут?"
        )
        return
    
    # Пользователь есть в базе
    user_name, user_workplace = user
    
    # Если нет активного состояния
    if current_state is None:
        await state.update_data(name=user_name, workplace=user_workplace)
        await state.set_state(Form.problem)
        
        # Отправляем сообщение с клавиатурой
        await message.answer(
            f"👋 С возвращением, {user_name}!",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Отправляем клавиатуру с проблемами
        await message.answer(
            "Выберите проблему:",
            reply_markup=get_problem_keyboard()
        )
        return
    
    # Если состояние есть, но сообщение не обработано другими хэндлерами
    if current_state == Form.problem.state:
        await message.answer(
            "Пожалуйста, выберите проблему из списка, используя кнопки:",
            reply_markup=get_problem_keyboard()
        )
        return

# --- ЗАПУСК БОТА ---
async def main():
    print("="*50)
    print("🚀 Бот для вызова сисадмина запущен!")
    print(f"👤 Админ ID: {ADMIN_ID}")
    print("="*50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
