import telebot
import os

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')  # Токен подтянется с хостинга
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я работаю на Bothost.ru 24/7!")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, f"Ты написал: {message.text}")

bot.infinity_polling()