import cv2
import numpy as np
import os
import time
import threading
import requests
import json
import mediapipe as mp
import websocket
import datetime

from flask import Flask, Response, request, jsonify

# ------------------ تنظیمات Flask ------------------
app = Flask(__name__)

# متغیر سراسری برای ذخیره آخرین فریم پردازش‌شده
output_frame = None
frame_lock = threading.Lock()

# ------------------ تنظیمات وب‌سوکت کلاینت ------------------
WS_URL = "ws://services.fin2.chabokan.net:29434/ws"  # آدرس سرور وب‌سوکت خارجی

# رنگ پیش‌فرض (آبی)
current_color = (255, 0, 0)  # فرمت BGR
color_lock = threading.Lock()

# متغیرهای رنگ
selected_color = current_color
last_received_color = current_color

# تابع مدیریت پیام‌های وب‌سوکت
def on_message(ws, message):
    global current_color, selected_color, last_received_color
    try:
        msg = json.loads(message)
        if "color" in msg:
            col = msg["color"]
            colors_dict = {
                "red": (0, 0, 255),
                "bright_orange": (0, 165, 255),
                "orange": (0, 140, 255),
                "green": (0, 255, 0),
                "yellow": (0, 255, 255),
                "purple": (255, 0, 255),
                "brown": (19, 69, 139),
                "pink": (203, 192, 255),
                "blue": (255, 0, 0),
                "black": (0, 0, 0),
                "white": (255, 255, 255)
            }
            new_color = colors_dict.get(col, current_color)
            if new_color != last_received_color:
                with color_lock:
                    current_color = new_color
                    selected_color = new_color
                last_received_color = new_color
                print(f"رنگ جدید از WS دریافت شد: {col} -> {new_color}")
    except Exception as e:
        print(f"خطا در پردازش پیام وب‌سوکت: {e}")

def on_error(ws, error):
    print(f"خطای وب‌سوکت: {error}")

def on_close(ws, close_status_code, close_msg):
    print("اتصال وب‌سوکت بسته شد.")

def on_open(ws):
    print("اتصال وب‌سوکت برقرار شد.")

def ws_client_thread():
    ws = websocket.WebSocketApp(WS_URL,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close,
                                on_open=on_open)
    ws.run_forever()

# ------------------ کلاس MJPEGStreamReader ------------------
class MJPEGStreamReader:
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()
        self.running = True
        self.frame = None
        self.frame_lock = threading.Lock()
        self.thread = threading.Thread(target=self._read_stream, daemon=True)
        self.thread.start()
    
    def _read_stream(self):
        while self.running:
            try:
                with self.session.get(self.url, stream=True, timeout=10) as response:
                    response.raise_for_status()
                    buffer = b""
                    for chunk in response.iter_content(chunk_size=4096):
                        if not self.running:
                            break
                        buffer += chunk
                        start = buffer.find(b'\xff\xd8')
                        end = buffer.find(b'\xff\xd9')
                        if start != -1 and end != -1 and end > start:
                            jpg = buffer[start:end+2]
                            with self.frame_lock:
                                self.frame = jpg
                            buffer = buffer[end+2:]
            except requests.exceptions.RequestException as e:
                print(f"خطا در دریافت استریم، در حال تلاش مجدد... {e}")
                time.sleep(1)
    
    def get_frame(self):
        with self.frame_lock:
            return self.frame
    
    def stop(self):
        self.running = False
        self.session.close()

# ------------------ کلاس Detector (تشخیص دست) ------------------
class Detector:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackingCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackingCon = trackingCon
        self.mediapipeHands = mp.solutions.hands
        self.hands = self.mediapipeHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackingCon
        )
        self.Draw = mp.solutions.drawing_utils
        self.Indexes = [4, 8, 12, 16, 20]  # نقاط انگشتان
    
    def findHands(self, frame, draw=True):
        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(frameRGB)
        if self.results.multi_hand_landmarks:
            for handlandmarks, hand in zip(self.results.multi_hand_landmarks, self.results.multi_handedness):
                if draw:
                    self.Draw.draw_landmarks(frame, handlandmarks, self.mediapipeHands.HAND_CONNECTIONS)
        return frame
    
    def Position(self, frame, handNo=0, draw=True):
        landmarkList = []
        if self.results.multi_hand_landmarks:
            myHands = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHands.landmark):
                h, w, c = frame.shape
                x, y = int(lm.x * w), int(lm.y * h)
                landmarkList.append([id, x, y])
                if draw:
                    cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
        return landmarkList
    
    def fing_up(self, handLandmarks):
        fingers = []
        if not handLandmarks:
            return [0] * 5
        for index in range(1, 5):
            if handLandmarks[self.Indexes[index]][2] < handLandmarks[self.Indexes[index]-2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        if handLandmarks[self.Indexes[0]][1] > handLandmarks[self.Indexes[0]-2][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        return fingers
    
    def is_thumb_index_touched(self, landmarks, threshold=30):
        if not landmarks or len(landmarks) < 21:
            return False
        thumb_tip = landmarks[4]  # نوک شست
        index_tip = landmarks[8]  # نوک اشاره
        distance = np.sqrt((thumb_tip[1] - index_tip[1]) ** 2 + (thumb_tip[2] - index_tip[2]) ** 2)
        return distance < threshold

# ------------------ تنظیمات مسیر و تولبار ------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_PATH = os.path.join(BASE_DIR, "static", "gallery")
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)
TOOLBAR_PATH = os.path.join(BASE_DIR, "toolbar")
toolbars = os.listdir(TOOLBAR_PATH)
toolbar = [cv2.imread(os.path.join(TOOLBAR_PATH, tool))
           for tool in toolbars if cv2.imread(os.path.join(TOOLBAR_PATH, tool)) is not None]
if len(toolbar) == 0:
    raise ValueError("تصاویر ابزار پیدا نشد یا به درستی بارگذاری نشدند.")

# تغییر اندازه منو به ابعاد (1280, 125)
menu = cv2.resize(toolbar[0], (1280, 125))

# تغییر اندازه تصاویر افزایش و کاهش ضخامت به ابعاد مناسب (350,150)
if len(toolbar) > 5:
    thicknessup = cv2.resize(toolbar[5], (150, 350))
else:
    thicknessup = None
if len(toolbar) > 4:
    thicknessdown = cv2.resize(toolbar[4], (150, 350))
else:
    thicknessdown = None
thick = thicknessup if thicknessup is not None else thicknessdown

colors = {"purple": (255, 0, 255), "green": (0, 255, 0), "red": (0, 0, 255), "blue": (255, 0, 0), "black": (0, 0, 0)}
color = colors["blue"]
with color_lock:
    selected_color = current_color

detector = Detector(detectionCon=0.7, maxHands=2)
blank = np.zeros((720, 1280, 3), np.uint8)  # بوم خالی
thickness = 15
stream_url = "http://services.fin2.chabokan.net:59743/video_feed"
stream_reader = MJPEGStreamReader(stream_url)

# متغیرهای وضعیت رسم
x0, y0 = 0, 0
ready_to_save = False
running = True

def process_frame():
    global x0, y0, color, ready_to_save, menu, thick, blank, running, thickness, selected_color, output_frame
    while running:
        jpg = stream_reader.get_frame()
        if jpg is None:
            time.sleep(0.01)
            continue
        nparr = np.frombuffer(jpg, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if frame is None:
            continue
        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (1280, 720))
        frame = detector.findHands(frame)
        all_hands = detector.results.multi_hand_landmarks if detector.results.multi_hand_landmarks else []
        handedness = detector.results.multi_handedness if detector.results.multi_handedness else []
        
        right_hand = []
        left_hand = []
        
        # تشخیص دست راست و چپ
        for idx, hand in enumerate(handedness):
            label = hand.classification[0].label
            if label == 'Right':
                right_hand = detector.Position(frame, handNo=idx, draw=False)
            elif label == 'Left':
                left_hand = detector.Position(frame, handNo=idx, draw=False)
        
        # پردازش دست راست برای نقاشی
        if len(right_hand) != 0:
            fin_pos_right = detector.fing_up(right_hand)
            x1, y1 = right_hand[8][1], right_hand[8][2]  # مختصات نوک انگشت اشاره
            x2, y2 = right_hand[12][1], right_hand[12][2]  # مختصات انگشت میانی
            if detector.is_thumb_index_touched(right_hand):
                # ذخیره تصویر
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = os.path.join(SAVE_PATH, f"drawing_{timestamp}.png")
                cv2.imwrite(save_path, blank)
                print(f"تصویر ذخیره شد: {save_path}")
                blank = np.zeros((720, 1280, 3), np.uint8)  # پاک کردن بوم
                try:
                    response = requests.post("http://localhost:7000/save_drawing", json={"status": "success", "message": "تصویر با موفقیت ذخیره شد"})
                    if response.status_code == 200:
                        green_frame = frame.copy()
                        green_overlay = np.zeros_like(green_frame)
                        green_overlay[:] = (0, 255, 0)
                        cv2.addWeighted(green_overlay, 0.3, green_frame, 0.7, 0, green_frame)
                        ret, buffer = cv2.imencode('.jpg', green_frame)
                        if ret:
                            with frame_lock:
                                output_frame = buffer.tobytes()
                        time.sleep(0.5)
                except Exception as e:
                    print(f"خطا در ارسال درخواست POST: {e}")
            if fin_pos_right[0] and fin_pos_right[1]:  # شست و اشاره بالا
                x0, y0 = 0, 0
                if x1 > 1133 and 125 < y1 < 472:
                    if 125 <= y1 < 300:
                        thick = thicknessup
                        thickness = 15
                    elif 300 <= y1 < 472:
                        thick = thicknessdown
                        thickness = 30
                if y1 < 125:  # انتخاب رنگ از تولبار
                    if 250 < x1 < 450:
                        color = colors["blue"]
                        menu = cv2.resize(toolbar[0], (1280, 125))
                        selected_color = color
                    elif 550 < x1 < 750:
                        color = colors["purple"]
                        menu = cv2.resize(toolbar[0], (1280, 125))
                        selected_color = color
                    elif 800 < x1 < 950:
                        color = colors["green"]
                        menu = cv2.resize(toolbar[0], (1280, 125))
                        selected_color = color
                    elif 1050 < x1 < 1200:
                        color = colors["black"]
                        menu = cv2.resize(toolbar[0], (1280, 125))
                        selected_color = color
                cv2.rectangle(frame, (x1, y1 - 20), (x2, y2 + 20), color, -1)
            if fin_pos_right[0] and not fin_pos_right[1]:  # فقط شست بالا
                if x0 == 0 and y0 == 0:
                    x0, y0 = x1, y1
                if 0 <= x1 < 1280 and 0 <= y1 < 720:
                    current_draw_color = selected_color
                    cv2.circle(frame, (x1, y1), 12, current_draw_color, -1)
                    if current_draw_color == colors["black"]:
                        cv2.line(frame, (x0, y0), (x1, y1), current_draw_color, thickness + 25)
                        cv2.line(blank, (x0, y0), (x1, y1), current_draw_color, thickness + 25)
                    else:
                        cv2.line(frame, (x0, y0), (x1, y1), current_draw_color, thickness)
                        cv2.line(blank, (x0, y0), (x1, y1), current_draw_color, thickness)
                    x0, y0 = x1, y1
        
        # پردازش دست چپ برای پاک کردن بوم
        if len(left_hand) != 0:
            fin_pos_left = detector.fing_up(left_hand)
            if all(finger == 1 for finger in fin_pos_left) and len(fin_pos_left) == 5:
                if ready_to_save:
                    blank = np.zeros((720, 1280, 3), np.uint8)
                    ready_to_save = False
            else:
                ready_to_save = True
        else:
            ready_to_save = True
        
        Gray = cv2.cvtColor(blank, cv2.COLOR_BGR2GRAY)
        _, Inv = cv2.threshold(Gray, 0, 255, cv2.THRESH_BINARY_INV)
        Inv = cv2.cvtColor(Inv, cv2.COLOR_GRAY2BGR)
        frame = cv2.bitwise_and(frame, Inv)
        frame = cv2.bitwise_or(frame, blank)
        
        # درج منو در بالای فریم؛ منو از قبل به اندازه (1280,125) تغییر اندازه یافته است.
        frame[0:125, 0:1280] = menu
        
        if thick is not None:
            frame[125:475, 1130:1280] = thick
        
        ret, buffer = cv2.imencode('.jpg', frame)
        if ret:
            with frame_lock:
                output_frame = buffer.tobytes()
        time.sleep(0.01)

threading.Thread(target=process_frame, daemon=True).start()
threading.Thread(target=ws_client_thread, daemon=True).start()

# ------------------ مسیرهای Flask ------------------
@app.route('/')
def index():
    return """
    <html>
    <head>
        <title>استریم نقاشی</title>
    </head>
    <body style="margin:0; padding:0; background-color:black;">
        <img src="/video_feed" style="display:block; width:100%; height:auto;">
    </body>
    </html>
    """

@app.route('/save_drawing', methods=['POST'])
def save_drawing():
    return jsonify({'status': 'success', 'message': 'تصویر با موفقیت ذخیره شد'})

def generate():
    global output_frame
    while True:
        with frame_lock:
            if output_frame is None:
                continue
            frame = output_frame
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.03)

@app.route('/video_feed')
def video_feed():
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7100, debug=False)
