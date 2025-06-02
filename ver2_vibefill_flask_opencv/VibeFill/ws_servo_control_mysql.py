from flask import Flask, render_template, request, jsonify, url_for, Response
from flask_cors import CORS
from flask_sock import Sock
import sqlite3
import datetime
import json
import os
import time
import numpy as np
import cv2
from queue import Queue
from threading import Lock

app = Flask(__name__)
CORS(app)
sock = Sock(app)

# نام فایل دیتابیس SQLite
DB_FILE = "servo_commands.db"

# متغیرهای جهانی برای مدیریت فریم‌های ESP32-CAM
esp32_frame_queue = Queue(maxsize=1)
frame_lock = Lock()
latest_frame = None

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """ایجاد دیتابیس و جداول servo_commands، color_commands، action_commands و device_mode_commands"""
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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS color_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                color TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed INTEGER DEFAULT 0
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS action_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed INTEGER DEFAULT 0
            );
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS device_mode_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_mode TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed INTEGER DEFAULT 0
            );
        """)
        conn.commit()
        print("✅ دیتابیس و جداول ایجاد شدند یا موجود بودند.")
    except Exception as e:
        print("❌ خطا در ایجاد دیتابیس/جدول:", e)
    finally:
        conn.close()

init_db()

def insert_servo_command(servo1, servo2):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO servo_commands (servo1, servo2) VALUES (?, ?)", (servo1, servo2))
        conn.commit()
        return True
    except Exception as e:
        print("❌ خطا در درج دستور سروو:", e)
        return False
    finally:
        conn.close()

def insert_color_command(color):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO color_commands (color) VALUES (?)", (color,))
        conn.commit()
        print(f"✅ رنگ '{color}' در جدول ثبت شد.")
        return True
    except Exception as e:
        print("❌ خطا در درج دستور رنگ:", e)
        return False
    finally:
        conn.close()

def insert_action_command(action):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO action_commands (action) VALUES (?)", (action,))
        conn.commit()
        print(f"✅ اقدام '{action}' در جدول ثبت شد.")
        return True
    except Exception as e:
        print("❌ خطا در درج دستور اقدام:", e)
        return False
    finally:
        conn.close()

def insert_device_mode_command(device_mode):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO device_mode_commands (device_mode) VALUES (?)", (device_mode,))
        conn.commit()
        print(f"✅ حالت دستگاه '{device_mode}' در جدول ثبت شد.")
        return True
    except Exception as e:
        print("❌ خطا در درج دستور حالت دستگاه:", e)
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
        return jsonify({'status': 'success', 'message': f'دستور سروو ثبت شد: X={servo1_val}°, Y={servo2_val}°'})
    else:
        return jsonify({'status': 'error', 'message': 'خطا در درج دستور در دیتابیس'})

@app.route('/set_color', methods=['POST'])
def set_color():
    data = request.get_json()
    color = data.get('color')
    if not color:
        return jsonify({'status': 'error', 'message': 'رنگ مشخص نشده است'})
    if insert_color_command(color):
        for ws in clients.copy():
            try:
                ws.send(json.dumps({"color": color, "timestamp": datetime.datetime.now().isoformat()}))
            except Exception as e:
                print("❌ خطا در ارسال به وب‌سوکت:", e)
        return jsonify({'status': 'success', 'message': f'رنگ {color} ثبت شد'})
    else:
        return jsonify({'status': 'error', 'message': 'خطا در درج رنگ در دیتابیس'})

@app.route('/set_action', methods=['POST'])
def set_action():
    data = request.get_json()
    action = data.get('action')
    if not action:
        return jsonify({'status': 'error', 'message': 'اقدام مشخص نشده است'})
    if insert_action_command(action):
        for ws in clients.copy():
            try:
                ws.send(json.dumps({"action": action, "timestamp": datetime.datetime.now().isoformat()}))
            except Exception as e:
                print("❌ خطا در ارسال به وب‌سوکت:", e)
        return jsonify({'status': 'success', 'message': f'اقدام {action} ثبت شد'})
    else:
        return jsonify({'status': 'error', 'message': 'خطا در درج اقدام در دیتابیس'})

@app.route('/set_device_mode', methods=['POST'])
def set_device_mode():
    data = request.get_json()
    device_mode = data.get('device_mode')
    if not device_mode or device_mode not in ['desktop', 'mobile']:
        return jsonify({'status': 'error', 'message': 'حالت دستگاه نامعتبر است'})
    if insert_device_mode_command(device_mode):
        for ws in clients.copy():
            try:
                ws.send(json.dumps({"device_mode": device_mode, "timestamp": datetime.datetime.now().isoformat()}))
            except Exception as e:
                print("❌ خطا در ارسال به وب‌سوکت:", e)
        return jsonify({'status': 'success', 'message': f'حالت دستگاه {device_mode} ثبت شد'})
    else:
        return jsonify({'status': 'error', 'message': 'خطا در درج حالت دستگاه در دیتابیس'})

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
    page = int(request.args.get('page', 0))
    limit = int(request.args.get('limit', 6))
    offset = page * limit
    selected = images[offset:offset + limit]
    image_urls = [url_for('static', filename=f'gallery/{img}') for img in selected]
    has_more = len(images) > offset + limit
    return jsonify({'image_urls': image_urls, 'has_more': has_more})

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

@app.route('/save_drawing', methods=['POST'])
def save_drawing():
    data = request.get_json()
    status = data.get('status')
    message = data.get('message')
    for ws in clients.copy():
        try:
            ws.send(json.dumps({"type": "toast", "status": status, "message": message}))
        except Exception as e:
            print("❌ خطا در ارسال به وب‌سوکت:", e)
    return jsonify({'status': 'success', 'message': 'اعلان ارسال شد'})

@app.route('/esp32_frame')
def esp32_frame():
    global latest_frame
    with frame_lock:
        if latest_frame is None:
            return Response(status=503)  # Service Unavailable
        ret, buffer = cv2.imencode('.jpg', latest_frame)
        return Response(buffer.tobytes(), mimetype='image/jpeg')

@app.route('/esp32_video_feed')
def esp32_video_feed():
    def generate():
        global latest_frame
        while True:
            with frame_lock:
                if latest_frame is None:
                    continue
                ret, buffer = cv2.imencode('.jpg', latest_frame)
                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.1)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@sock.route('/ws')
def websocket(ws):
    global latest_frame
    clients.append(ws)
    print("یک کلاینت وب‌سوکت متصل شد. تعداد:", len(clients))
    try:
        while True:
            data = ws.receive()
            if data is None:
                break
            try:
                # بررسی اگر داده باینری (فریم از ESP32-CAM) باشد
                if isinstance(data, bytes):
                    img = np.frombuffer(data, dtype=np.uint8)
                    frame = cv2.imdecode(img, cv2.IMREAD_COLOR)
                    if frame is not None:
                        with frame_lock:
                            latest_frame = frame
                            if esp32_frame_queue.full():
                                esp32_frame_queue.get()
                            esp32_frame_queue.put(frame)
                else:
                    # پردازش پیام‌های JSON
                    msg = json.loads(data)
                    if 'servo1' in msg and 'servo2' in msg:
                        servo1 = int(msg.get('servo1', 90))
                        servo2 = int(msg.get('servo2', 90))
                        if 0 <= servo1 <= 180 and 0 <= servo2 <= 180:
                            insert_servo_command(servo1, servo2)
                            for client in clients.copy():
                                try:
                                    client.send(json.dumps({"servo1": servo1, "servo2": servo2, "timestamp": datetime.datetime.now().isoformat()}))
                                except Exception as e:
                                    print("❌ خطا در ارسال به کلاینت وب‌سوکت:", e)
                    elif 'color' in msg:
                        color = msg.get("color")
                        print("📥 دریافت دستور رنگ:", color)
                        insert_color_command(color)
                        for client in clients.copy():
                            try:
                                client.send(json.dumps({"color": color, "timestamp": datetime.datetime.now().isoformat()}))
                            except Exception as e:
                                print("❌ خطا در ارسال به کلاینت وب‌سوکت:", e)
                    elif 'action' in msg:
                        action = msg.get("action")
                        print("📥 دریافت دستور اقدام:", action)
                        insert_action_command(action)
                        for client in clients.copy():
                            try:
                                client.send(json.dumps({"action": action, "timestamp": datetime.datetime.now().isoformat()}))
                            except Exception as e:
                                print("❌ خطا در ارسال به کلاینت وب‌سوکت:", e)
                    elif 'device_mode' in msg:
                        device_mode = msg.get("device_mode")
                        if device_mode in ['desktop', 'mobile']:
                            print("📥 دریافت دستور حالت دستگاه:", device_mode)
                            insert_device_mode_command(device_mode)
                            for client in clients.copy():
                                try:
                                    client.send(json.dumps({"device_mode": device_mode, "timestamp": datetime.datetime.now().isoformat()}))
                                except Exception as e:
                                    print("❌ خطا در ارسال به کلاینت وب‌سوکت:", e)
                        else:
                            print("❌ حالت دستگاه نامعتبر:", device_mode)
            except Exception as e:
                print("❌ خطا در پردازش پیام وب‌سوکت:", e)
    except Exception as e:
        print("❌ خطا در وب‌سوکت:", e)
    finally:
        clients.remove(ws)
        print("یک کلاینت وب‌سوکت قطع شد. تعداد:", len(clients))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, threaded=True)