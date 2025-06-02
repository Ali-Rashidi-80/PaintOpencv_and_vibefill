from flask import Flask, render_template, request, jsonify, url_for
from flask_cors import CORS
from flask_sock import Sock
import sqlite3
import datetime
import json
import os

app = Flask(__name__)
CORS(app)
sock = Sock(app)

# نام فایل دیتابیس SQLite (در همان سرور)
DB_FILE = "servo_commands.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """ایجاد دیتابیس و جدول servo_commands در صورت عدم وجود"""
    conn = get_db_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS servo_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                servo1 INTEGER NOT NULL,
                servo2 INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed INTEGER DEFAULT 0
            );
        """)
        conn.commit()
        print("✅ دیتابیس و جدول servo_commands ایجاد شدند یا موجود بودند.")
    except Exception as e:
        print("❌ خطا در ایجاد دیتابیس/جدول:", e)
    finally:
        conn.close()

# فراخوانی init_db در زمان شروع برنامه
init_db()

def insert_servo_command(servo1, servo2):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO servo_commands (servo1, servo2) VALUES (?, ?)", (servo1, servo2))
        conn.commit()
        return True
    except Exception as e:
        print("❌ خطا در درج دستور:", e)
        return False
    finally:
        conn.close()

# لیست اتصال‌های وب‌سوکت فعال
clients = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_servo', methods=['POST'])
def set_servo():
    data = request.get_json() if request.is_json else request.form
    try:
        servo1_val = int(data.get('servo1') or data.get('servoX', 90))
        servo2_val = int(data.get('servo2') or data.get('servoY', 90))
    except Exception as e:
        return jsonify({'status': 'error', 'message': 'پارامترهای نامعتبر: ' + str(e)})
    
    if not (0 <= servo1_val <= 180 and 0 <= servo2_val <= 180):
        return jsonify({'status': 'error', 'message': 'زوایا باید بین 0 تا 180 باشند'})

    if insert_servo_command(servo1_val, servo2_val):
        command = {
            'servo1': servo1_val,
            'servo2': servo2_val,
            'timestamp': datetime.datetime.now().isoformat()
        }
        for ws in clients.copy():
            try:
                ws.send(json.dumps(command))
            except Exception as e:
                print("❌ خطا در ارسال به وب‌سوکت:", e)
        return jsonify({'status': 'success', 'message': f'دستور ثبت شد: X={servo1_val}°, Y={servo2_val}°'})
    else:
        return jsonify({'status': 'error', 'message': 'خطا در درج دستور در دیتابیس'})

@app.route('/get_status', methods=['GET'])
def get_status():
    conn = get_db_connection()
    try:
        cur = conn.execute("""
            SELECT servo1, servo2, created_at 
            FROM servo_commands 
            WHERE processed = 0 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        row = cur.fetchone()
        if row:
            return jsonify(dict(row))
        else:
            return jsonify({'servo1': 90, 'servo2': 90})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})
    finally:
        conn.close()

@app.route('/get_gallery')
def get_gallery():
    gallery_folder = os.path.join(app.static_folder, 'gallery')
    images = [f for f in os.listdir(gallery_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    images.sort(key=lambda x: os.path.getctime(os.path.join(gallery_folder, x)), reverse=True)
    offset = int(request.args.get('offset', 0))
    limit = 6
    selected = images[offset:offset+limit]
    image_urls = [url_for('static', filename=f'gallery/{img}') for img in selected]
    next_offset = offset + len(selected)
    return jsonify({'image_urls': image_urls, 'next_offset': next_offset})

@app.route('/delete_image', methods=['POST'])
def delete_image():
    data = request.get_json()
    filename = data.get('filename', '')
    if not filename:
        return jsonify({'status': 'error', 'message': 'نام فایل مشخص نشده است'})
    
    if "/" in filename:
        filename = filename.split('/')[-1]
    
    gallery_folder = os.path.join(app.static_folder, 'gallery')
    file_path = os.path.join(gallery_folder, filename)
    
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return jsonify({'status': 'success', 'message': 'تصویر حذف شد'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'خطا در حذف تصویر: {str(e)}'})
    else:
        return jsonify({'status': 'error', 'message': 'تصویر یافت نشد'})

@sock.route('/ws')
def websocket(ws):
    clients.append(ws)
    print("یک کلاینت وب‌سوکت متصل شد. تعداد:", len(clients))
    try:
        while True:
            data = ws.receive()
            if data is None:
                break
            # در صورت نیاز، پردازش پیام دریافتی
    except Exception as e:
        print("❌ خطا در وب‌سوکت:", e)
    finally:
        clients.remove(ws)
        print("یک کلاینت وب‌سوکت قطع شد. تعداد:", len(clients))
    return

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000)
