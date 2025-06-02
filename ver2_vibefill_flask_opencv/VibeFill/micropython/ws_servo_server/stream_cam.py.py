from flask import Flask, Response, render_template_string
from flask_sock import Sock
import time

app = Flask(__name__)
sock = Sock(app)

# متغیر سراسری جهت ذخیره آخرین فریم دریافتی از ESP32
latest_frame = None

# وب‌سوکت برای دریافت فریم‌های باینری از ESP32
@sock.route('/ws')
def ws_handler(ws):
    global latest_frame
    while True:
        data = ws.receive()  # دریافت داده (فریم باینری)
        if data is None:
            break  # در صورت قطع اتصال
        latest_frame = data  # به‌روزرسانی آخرین فریم

# صفحه اصلی وب با HTML داخلی
@app.route('/')
def index():
    html_content = """
    <!doctype html>
    <html lang="fa">
    <body>
        <img src="/video_feed" alt="Video Feed">
    </body>
    </html>
    """
    return render_template_string(html_content)

# تابع تولید کننده فریم‌ها به فرمت MJPEG
def gen_frames():
    global latest_frame
    while True:
        if latest_frame is None:
            time.sleep(0.1)
            continue
        # ارسال فریم به صورت بخش‌های MJPEG
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
        time.sleep(0.1)  # تنظیم فاصله بین ارسال فریم‌ها

# endpoint جهت ارائه استریم MJPEG به مرورگر
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # اجرای سرور Flask روی پورت 7200 (همان پورت مورد استفاده در ESP32)
    app.run(host='0.0.0.0', port=7200, debug=True)
