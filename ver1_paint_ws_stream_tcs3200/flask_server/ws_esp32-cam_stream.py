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
        data = ws.receive()
        if data is None:
            break
        latest_frame = data

# صفحه اصلی وب با HTML داخلی
@app.route('/')
def index():
    html_content = """
    <!doctype html>
    <html lang="fa">
    <head>
        <meta charset="utf-8">
        <title>استریم ویدیو</title>
    </head>
    <body style="margin:0; padding:0; background-color:black;">
        <img src="/video_feed" alt="Video Feed" style="width:100%; height:auto;">
    </body>
    </html>
    """
    return render_template_string(html_content)

# تابع تولید کننده فریم‌ها به فرمت MJPEG
def gen_frames():
    global latest_frame
    while True:
        if latest_frame is None:
            time.sleep(0.01)
            continue
        # ارسال فریم به صورت بخش‌های MJPEG
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + latest_frame + b'\r\n')
        # کاهش تاخیر بین ارسال فریم‌ها
        time.sleep(0.05)

# endpoint ارائه استریم MJPEG به مرورگر
@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    # استفاده از threaded=True برای پردازش همزمان درخواست‌ها
    app.run(host='0.0.0.0', port=7200, debug=False, threaded=True)
