from flask import Flask, request
import telebot
import os

app = Flask(__name__)

# Получаем переменные окружения
TOKEN = os.environ.get('BOT_TOKEN', '8364189800:AAHHsHHgKZ7oB6XSHExPWn0-0G5Fp8fGNi4')
CHAT_ID = os.environ.get('CHAT_ID', '7725796090')

bot = telebot.TeleBot(TOKEN)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    # Обработка данных
    return {"status": "ok"}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot is alive!")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
