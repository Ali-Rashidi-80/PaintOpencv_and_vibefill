import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import messagebox, filedialog
import requests
import threading
import time
import mediapipe as mp
from PIL import Image, ImageTk
import json
import websocket  # کتابخانه websocket-client

# ------------------ تنظیمات وب‌سوکت ------------------
WS_URL = "ws://services.fin2.chabokan.net:29434/ws"  # آدرس سرور وب‌سوکت

# رنگ پیش‌فرض (آبی)
current_color = (255, 0, 0)
color_lock = threading.Lock()

# متغیر سراسری برای رنگ انتخاب شده از تولبار یا وب‌سوکت (در ابتدا همان رنگ پیش‌فرض)
selected_color = current_color
# متغیر سراسری برای ذخیره آخرین رنگ دریافتی از وب‌سوکت
last_received_color = current_color

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
            # در صورت دریافت رنگ جدید (مختلف از آخرین رنگ وب‌سوکت دریافتی) به‌روزرسانی می‌کنیم.
            if new_color != last_received_color:
                with color_lock:
                    # این تغییر باعث می‌شود که حتی اگر کاربر رنگی به صورت دستی انتخاب کرده باشد،
                    # رنگ دریافتی از وب‌سوکت اولویت داشته باشد.
                    current_color = new_color
                    selected_color = new_color
                last_received_color = new_color
                print(f"رنگ جدید از WS دریافت شد: {col} -> {new_color}")
    except Exception as e:
        print("خطا در پردازش پیام وب‌سوکت:", e)

def on_error(ws, error):
    print("خطای وب‌سوکت:", error)

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
                print("خطا در دریافت استریم، در حال تلاش مجدد...", e)
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
        self.Indexes = [4, 8, 12, 16, 20]
        self.landmarkList = []
    
    def findHands(self, frame, draw=True):
        frameRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(frameRGB)
        if self.results.multi_hand_landmarks:
            for handlandmarks in self.results.multi_hand_landmarks:
                if draw:
                    self.Draw.draw_landmarks(frame, handlandmarks, self.mediapipeHands.HAND_CONNECTIONS)
        return frame
    
    def Position(self, frame, handNo=0, draw=True):
        self.landmarkList = []
        if self.results.multi_hand_landmarks:
            myHands = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHands.landmark):
                h, w, c = frame.shape
                x, y = int(lm.x * w), int(lm.y * h)
                self.landmarkList.append([id, x, y])
                if draw:
                    cv2.circle(frame, (x, y), 8, (0, 0, 255), -1)
        return self.landmarkList
    
    def fing_up(self):
        fingers = []
        if not self.landmarkList:
            return [0] * 5
        # بررسی وضعیت انگشتان (اندیس‌های 8، 12، 16، 20)
        for index in range(1, 5):
            if self.landmarkList[self.Indexes[index]][2] < self.landmarkList[self.Indexes[index]-2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
        # بررسی شست (اندیس 4)
        if self.landmarkList[self.Indexes[0]][1] > self.landmarkList[self.Indexes[0]-2][1]:
            fingers.append(1)
        else:
            fingers.append(0)
        return fingers

# ------------------ تابع بررسی نزدیک بودن انگشتان ------------------
def fingers_close(landmarks, threshold=50):
    if not landmarks or len(landmarks) < 21:
        return False
    indices = [4, 8, 12, 16, 20]
    pts = []
    for idx in indices:
        for lm in landmarks:
            if lm[0] == idx:
                pts.append((lm[1], lm[2]))
                break
    if len(pts) < len(indices):
        return False
    max_dist = 0
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            dist = np.sqrt((pts[i][0] - pts[j][0])**2 + (pts[i][1] - pts[j][1])**2)
            max_dist = max(max_dist, dist)
    return max_dist < threshold

# ------------------ تنظیمات مسیر و تولبار ------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_PATH = os.path.join(BASE_DIR, "drawings")
TOOLBAR_PATH = os.path.join(BASE_DIR, "toolbar")

toolbars = os.listdir(TOOLBAR_PATH)
toolbar = [cv2.imread(os.path.join(TOOLBAR_PATH, tool))
           for tool in toolbars if cv2.imread(os.path.join(TOOLBAR_PATH, tool)) is not None]
if len(toolbar) == 0:
    raise ValueError("تصاویر ابزار پیدا نشد یا به درستی بارگذاری نشدند.")

menu = toolbar[0]            # منوی اولیه
thicknessup = toolbar[5] if len(toolbar) > 5 else None    # تصویر افزایش ضخامت
thicknessdown = toolbar[4] if len(toolbar) > 4 else None  # تصویر کاهش ضخامت
thick = thicknessup if thicknessup is not None else thicknessdown

# دیکشنری رنگ‌های ثابت برای انتخاب دستی
colors = {
    "purple": (255, 0, 255),
    "green": (0, 255, 0),
    "red": (0, 0, 255),
    "blue": (255, 0, 0),
    "black": (0, 0, 0)
}

# تعریف متغیر color به عنوان رنگ اولیه (مثلاً آبی)
color = colors["blue"]

# به‌روزرسانی اولیه selected_color از طریق WS (اگر کاربر رنگی انتخاب نکرده باشد)
with color_lock:
    selected_color = current_color

detector = Detector(detectionCon=0.7, maxHands=2)
blank = np.zeros((720, 1280, 3), np.uint8)

# مقدار پیش‌فرض ضخامت قلم
thickness = 15

# ------------------ توابع ذخیره نقاشی ------------------
def save_drawing(image, save_path, filename):
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    full_path = os.path.join(save_path, filename)
    cv2.imwrite(full_path, image)
    print(f"Drawing saved at: {full_path}")

def confirm_save(image):
    temp_root = tk.Tk()
    temp_root.withdraw()
    answer = messagebox.askyesno("Save Drawing", "Do you want to save the drawing?")
    if answer:
        filename = filedialog.asksaveasfilename(
            title="Save Drawing As",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if filename:
            save_drawing(image, os.path.dirname(filename), os.path.basename(filename))
    temp_root.destroy()
    global blank
    blank = np.zeros((720, 1280, 3), np.uint8)

# ------------------ متغیرهای وضعیت ------------------
x0, y0 = 0, 0
ready_to_save = False
running = True
save_prompt_triggered = False
stream_url = "http://192.168.43.157:81"
stream_reader = MJPEGStreamReader(stream_url)

# ------------------ توابع کنترل برنامه ------------------
def quit_program():
    global running
    running = False
    if stream_reader is not None:
        stream_reader.stop()
    root.quit()

# ------------------ رابط گرافیکی Tkinter ------------------
root = tk.Tk()
root.title("Paint Application")
canvas_frame = tk.Frame(root)
canvas_frame.pack(padx=10, pady=10)
canvas_label = tk.Label(canvas_frame)
canvas_label.pack()
root.protocol("WM_DELETE_WINDOW", quit_program)

# ------------------ تابع پردازش فریم ------------------
def process_frame():
    global x0, y0, color, ready_to_save, save_prompt_triggered, menu, thick, blank, running, thickness, selected_color
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
        right_hand = detector.Position(frame, handNo=0, draw=False) if len(all_hands) > 0 else []
        
        if len(right_hand) != 0:
            fin_pos = detector.fing_up()  # وضعیت انگشتان دست
            # دریافت مختصات انگشت اشاره (اندیس 8) و انگشت وسط (اندیس 12)
            x1, y1 = right_hand[8][1], right_hand[8][2]
            x2, y2 = right_hand[12][1], right_hand[12][2]
            
            # حالت انتخاب ابزار: اگر انگشت اشاره و وسط بلند باشند
            if fin_pos[0] and fin_pos[1]:
                x0, y0 = 0, 0
                # ناحیه سمت راست برای تغییر ضخامت قلم
                if x1 > 1133 and 125 < y1 < 472:
                    if 125 <= y1 < 300:
                        thick = thicknessup
                        thickness = 15
                    elif 300 <= y1 < 472:
                        thick = thicknessdown
                        thickness = 30
                # نوار ابزار بالایی برای انتخاب رنگ
                if y1 < 125:
                    if 250 < x1 < 450:
                        color = colors["blue"]
                        menu = toolbar[0]
                        selected_color = color
                    elif 550 < x1 < 750:
                        color = colors["purple"]
                        menu = toolbar[1]
                        selected_color = color
                    elif 800 < x1 < 950:
                        color = colors["green"]
                        menu = toolbar[2]
                        selected_color = color
                    elif 1050 < x1 < 1200:
                        color = colors["black"]
                        menu = toolbar[3]
                        selected_color = color
                cv2.rectangle(frame, (x1, y1-20), (x2, y2+20), color, -1)
            
            # حالت نقاشی: تنها انگشت اشاره بالا
            if fin_pos[0] and not fin_pos[1]:
                if x0 == 0 and y0 == 0:
                    x0, y0 = x1, y1
                if 0 <= x1 < 1280 and 0 <= y1 < 720:
                    # استفاده از selected_color که ممکن است به روز شده باشد (حتی توسط WS)
                    current_draw_color = selected_color
                    cv2.circle(frame, (x1, y1), 12, current_draw_color, -1)
                    if current_draw_color == colors["black"]:
                        cv2.line(frame, (x0, y0), (x1, y1), current_draw_color, thickness + 25)
                        cv2.line(blank, (x0, y0), (x1, y1), current_draw_color, thickness + 25)
                    else:
                        cv2.line(frame, (x0, y0), (x1, y1), current_draw_color, thickness)
                        cv2.line(blank, (x0, y0), (x1, y1), current_draw_color, thickness)
                    x0, y0 = x1, y1
            
            # ذخیره‌سازی: اگر همه ۵ انگشت بالا باشند
            if all(finger == 1 for finger in fin_pos) and len(fin_pos) == 5:
                if ready_to_save:
                    confirm_save(blank)
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
        frame[0:125, 0:1280] = menu
        if thick is not None:
            frame[125:475, 1130:1280] = thick
        
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image = ImageTk.PhotoImage(image)
        canvas_label.config(image=image)
        canvas_label.image = image
        
        time.sleep(0.01)

threading.Thread(target=process_frame, daemon=True).start()
threading.Thread(target=ws_client_thread, daemon=True).start()
root.mainloop()
