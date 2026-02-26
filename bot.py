import asyncio
import sqlite3
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    ChatMemberUpdated
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.markdown import hbold

# ===== ТВОИ НАСТРОЙКИ =====
ADMIN_ID = 911966345  # Твой ID
BOT_TOKEN = os.getenv('BOT_TOKEN')

if not BOT_TOKEN:
    print("❌ Токен не найден!")
    exit(1)

# ===== НАСТРОЙКИ =====
DB_PATH = "users.db"

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== СОЗДАЁМ БОТА =====
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ===== БАЗА ДАННЫХ =====
class Database:
    @staticmethod
    def init_db():
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                workplace TEXT NOT NULL,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_blocked INTEGER DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_blocked ON users(is_blocked)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_active ON users(last_active)")
        conn.commit()
        conn.close()
        logger.info("✅ База данных сотрудников создана")

    @staticmethod
    def get_user(user_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, workplace, is_blocked FROM users WHERE user_id = ?", 
            (user_id,)
        )
        user = cursor.fetchone()
        conn.close()
        return