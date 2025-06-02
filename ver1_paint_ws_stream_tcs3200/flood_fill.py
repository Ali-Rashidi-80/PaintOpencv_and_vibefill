import cv2
import numpy as np
import mediapipe as mp
from screeninfo import get_monitors
from bidi.algorithm import get_display
import arabic_reshaper
from PIL import Image, ImageDraw, ImageFont
import time

# دریافت رزولوشن صفحه نمایش
try:
    monitor = get_monitors()[0]
    screen_width, screen_height = monitor.width, monitor.height
except:
    screen_width, screen_height = 1920, 1080

# تنظیمات هوشمند اندازه پنجره
max_window_width = int(screen_width * 0.8)
max_window_height = int(screen_height * 0.8)

# تنظیمات اولیه Mediapipe
mp_drawing = mp.solutions.drawing_utils
mp_hands = mp.solutions.hands

# بارگذاری فونت B Yekan
font_path = "BYekan_p30download.com.ttf"
try:
    font = ImageFont.truetype(font_path, 22)
except:
    raise ValueError("فایل فونت B Yekan یافت نشد یا بارگذاری نشد.")

# بارگذاری عکس آرت‌ورک
artwork_path = '4.png'
artwork = cv2.imread(artwork_path)
if artwork is None:
    raise ValueError("عکس آرت‌ورک بارگذاری نشد.")

# تغییر اندازه عکس آرت‌ورک
artwork_width, artwork_height = 600, 450
artwork = cv2.resize(artwork, (artwork_width, artwork_height))

# افزودن پدینگ به تصویر آرت‌ورک
padding = 150
artwork_padded = cv2.copyMakeBorder(artwork, padding, padding, padding, padding, cv2.BORDER_CONSTANT, value=(255, 255, 255))
canvas = artwork_padded.copy()

# ایجاد ماسک برای نواحی مشکی
gray = cv2.cvtColor(artwork_padded, cv2.COLOR_BGR2GRAY)
_, black_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)

# تنظیمات دوربین
cap = cv2.VideoCapture(0)
cam_width, cam_height = 550, 300
cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)

# نوار رنگی و اطلاعات رنگ‌ها
color_bar_height = 40
colors = {
    (0, 0, 255): {"name": "قرمز", "text_color": (200, 0, 0), "border_color": (200, 0, 0)},
    (0, 255, 0): {"name": "سبز", "text_color": (0, 180, 0), "border_color": (0, 180, 0)},
    (255, 0, 0): {"name": "آبی", "text_color": (0, 0, 200), "border_color": (0, 0, 200)},
    (0, 255, 255): {"name": "زرد", "text_color": (180, 180, 0), "border_color": (180, 180, 0)},
    (0, 0, 0): {"name": "پاکن", "text_color": (255, 255, 255), "border_color": (200, 0, 0)}
}
color_bar = np.zeros((color_bar_height, cam_width, 3), dtype=np.uint8)
x_offset = 0
color_width = cam_width // len(colors)
for color in colors:
    color_bar[:, x_offset:x_offset+color_width] = color
    x_offset += color_width

# اطلاعات عملیات
operations = {
    "undo": {"name": "بازگشت", "text_color": (255, 140, 0), "border_color": (255, 140, 0)},
    "reset": {"name": "ریست", "text_color": (128, 0, 128), "border_color": (128, 0, 128)}
}

# متغیرهای جهانی
selected_color = None
coloring_enabled = False
finger_positions = []
filter_size = 12
pinch_threshold = 0.05
undo_stack = []
initial_canvas = canvas.copy()
ema_x, ema_y = None, None
alpha = 0.3
undo_active = False
reset_active = False
last_undo_time = 0
last_reset_time = 0
gesture_debounce = 0.5

# متغیرهای انیمیشن
animation_states = {
    "color": {"start_time": 0, "progress": 0, "last_color": None},
    "undo": {"start_time": 0, "progress": 0},
    "reset": {"start_time": 0, "progress": 0}
}
animation_duration = 0.3  # مدت زمان انیمیشن (ثانیه)

# کش اندازه متن‌ها
text_sizes = {}
def get_text_size(text, font):
    if text not in text_sizes:
        pil_image = Image.new('RGB', (100, 100))
        draw = ImageDraw.Draw(pil_image)
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        text_bbox = draw.textbbox((0, 0), bidi_text, font=font)
        text_sizes[text] = (text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1])
    return text_sizes[text]

# تابع تشخیص ژست pinch
def detect_pinch(hand_landmarks, finger1, finger2):
    tip1 = hand_landmarks.landmark[finger1]
    tip2 = hand_landmarks.landmark[finger2]
    distance = np.linalg.norm(
        np.array([tip1.x, tip1.y]) - 
        np.array([tip2.x, tip2.y])
    )
    return distance < pinch_threshold

# تابع برای محاسبه پیشرفت انیمیشن
def get_animation_progress(start_time, duration):
    elapsed = time.time() - start_time
    progress = min(elapsed / duration, 1.0)
    return progress

# تابع برای نمایش متن فارسی با انیمیشن
def draw_persian_text_pil(image, text, position, font, text_color, bg_color=(0, 0, 0, 128), border_color=None, anim_progress=1.0):
    pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image, 'RGBA')
    
    # آماده‌سازی متن فارسی
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)

    # محاسبه اندازه متن
    text_w, text_h = get_text_size(text, font)
    text_x, text_y = position

    # انیمیشن: تغییر شفافیت و مقیاس
    alpha = int(255 * anim_progress)  # شفافیت از 0 به 255
    scale = 1.0 + 0.2 * (1.0 - anim_progress)  # مقیاس از 1.2 به 1.0
    bg_alpha = int(128 * anim_progress)  # شفافیت پس‌زمینه

    # انیمیشن تغییر رنگ کادر
    if border_color:
        start_border_color = (100, 100, 100)  # خاکستری برای شروع
        border_color = tuple(
            int(start_border_color[i] + (border_color[i] - start_border_color[i]) * anim_progress)
            for i in range(3)
        ) + (alpha,)

    # محاسبه ابعاد کادر با مقیاس
    margin = 10
    scaled_w = text_w * scale
    scaled_h = text_h * scale
    offset_x = (scaled_w - text_w) / 2
    offset_y = (scaled_h - text_h) / 2

    # کادر پس‌زمینه نیمه‌شفاف با گوشه‌های گرد
    draw.rounded_rectangle(
        (text_x-margin-offset_x, text_y-margin-offset_y, text_x+text_w+margin+offset_x, text_y+text_h+margin+offset_y),
        radius=5,
        fill=(bg_color[0], bg_color[1], bg_color[2], bg_alpha)
    )
    
    # کادر دور متن
    if border_color:
        draw.rounded_rectangle(
            (text_x-margin-offset_x, text_y-margin-offset_y, text_x+text_w+margin+offset_x, text_y+text_h+margin+offset_y),
            radius=5,
            outline=border_color,
            width=1
        )

    # رسم متن با شفافیت
    draw.text((text_x, text_y), bidi_text, font=font, fill=(text_color[0], text_color[1], text_color[2], alpha))

    # تبدیل به OpenCV
    image[:] = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

# حلقه اصلی
with mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7) as hands:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame = cv2.resize(frame, (cam_width, cam_height))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # تشخیص دست و لندمارک‌ها
        hands_results = hands.process(rgb_frame)
        x_avg, y_avg = None, None
        undo_active = False
        reset_active = False
        current_time = time.time()

        if hands_results.multi_hand_landmarks:
            for hand_landmarks in hands_results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                index_finger_tip = hand_landmarks.landmark[8]
                h, w, _ = frame.shape
                x, y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                
                # ذخیره مختصات و محاسبه میانگین
                finger_positions.append((x, y))
                if len(finger_positions) > filter_size:
                    finger_positions.pop(0)
                
                x_mean = np.mean([pos[0] for pos in finger_positions])
                y_mean = np.mean([pos[1] for pos in finger_positions])

                # اعمال میانگین متحرک نمایی
                if ema_x is None or ema_y is None:
                    ema_x, ema_y = x_mean, y_mean
                else:
                    ema_x = alpha * x_mean + (1 - alpha) * ema_x
                    ema_y = alpha * y_mean + (1 - alpha) * ema_y
                
                x_avg, y_avg = int(ema_x), int(ema_y)

                # انتخاب رنگ از نوار بالایی
                if 0 <= x_avg < cam_width and y_avg < color_bar_height:
                    new_color = tuple(map(int, color_bar[0, x_avg]))
                    if new_color != animation_states["color"]["last_color"]:
                        animation_states["color"]["start_time"] = current_time
                        animation_states["color"]["last_color"] = new_color
                    selected_color = new_color

                # تشخیص ژست‌ها
                if detect_pinch(hand_landmarks, 4, 8):
                    coloring_enabled = True
                else:
                    coloring_enabled = False

                if detect_pinch(hand_landmarks, 4, 20) and current_time - last_undo_time > gesture_debounce:
                    undo_active = True
                    last_undo_time = current_time
                    animation_states["undo"]["start_time"] = current_time
                    if undo_stack:
                        canvas = undo_stack.pop()
                        artwork_padded = canvas.copy()

                if detect_pinch(hand_landmarks, 4, 12) and current_time - last_reset_time > gesture_debounce:
                    reset_active = True
                    last_reset_time = current_time
                    animation_states["reset"]["start_time"] = current_time
                    canvas = initial_canvas.copy()
                    artwork_padded = canvas.copy()
                    undo_stack.clear()

                # نمایش رنگ انتخاب‌شده و عملیات در سمت راست
                text_x = cam_width - 120
                if selected_color:
                    color_info = colors.get(selected_color, {"name": "ناشناخته", "text_color": (255, 255, 255), "border_color": None})
                    color_name = color_info["name"]
                    text_color = color_info["text_color"]
                    border_color = color_info["border_color"]
                    anim_progress = get_animation_progress(animation_states["color"]["start_time"], animation_duration)
                    draw_persian_text_pil(
                        frame,
                        f"رنگ: {color_name}",
                        (text_x, 50),
                        font,
                        text_color=text_color,
                        border_color=border_color,
                        anim_progress=anim_progress
                    )

                # نمایش عملیات
                if undo_active:
                    anim_progress = get_animation_progress(animation_states["undo"]["start_time"], animation_duration)
                    draw_persian_text_pil(
                        frame,
                        operations["undo"]["name"],
                        (text_x, 85),
                        font,
                        text_color=operations["undo"]["text_color"],
                        border_color=operations["undo"]["border_color"],
                        anim_progress=anim_progress
                    )
                if reset_active:
                    anim_progress = get_animation_progress(animation_states["reset"]["start_time"], animation_duration)
                    draw_persian_text_pil(
                        frame,
                        operations["reset"]["name"],
                        (text_x, 120),
                        font,
                        text_color=operations["reset"]["text_color"],
                        border_color=operations["reset"]["border_color"],
                        anim_progress=anim_progress
                    )

        # ترکیب نوار رنگی با صفحه دوربین
        frame_with_bar = np.vstack((color_bar, frame))

        # نمایش نشانگر روی صفحه آرت‌ورک
        artwork_display = artwork_padded.copy()
        if hands_results.multi_hand_landmarks and x_avg is not None:
            x_art = int(x_avg * (artwork_padded.shape[1] / w))
            y_art = int(y_avg * (artwork_padded.shape[0] / h))
            cv2.circle(artwork_display, (x_art, y_art), 5, (0, 0, 255), -1)

            # اعمال رنگ‌آمیزی یا پاک کردن
            if coloring_enabled and selected_color:
                if 0 <= x_art < canvas.shape[1] and 0 <= y_art < canvas.shape[0]:
                    if black_mask[y_art, x_art] == 0:
                        undo_stack.append(canvas.copy())
                        mask = np.zeros((canvas.shape[0] + 2, canvas.shape[1] + 2), dtype=np.uint8)
                        mask[1:-1, 1:-1] = black_mask
                        fill_color = (255, 255, 255) if selected_color == (0, 0, 0) else selected_color
                        cv2.floodFill(
                            canvas, 
                            mask, 
                            (x_art, y_art), 
                            fill_color, 
                            loDiff=(150, 150, 150), 
                            upDiff=(150, 150, 150), 
                            flags=cv2.FLOODFILL_FIXED_RANGE
                        )
                        artwork_padded = canvas.copy()

        # تنظیم اندازه frame_with_bar برای مطابقت با ارتفاع artwork_display
        frame_with_bar = cv2.resize(frame_with_bar, (cam_width, artwork_display.shape[0]))

        # ترکیب افقی دو تصویر
        combined_frame = np.hstack((frame_with_bar, artwork_display))

        # تنظیم هوشمند اندازه پنجره ترکیبی
        window_width = combined_frame.shape[1]
        window_height = combined_frame.shape[0]
        if window_width > max_window_width or window_height > max_window_height:
            scale = min(max_window_width / window_width, max_window_height / window_height)
            new_width = int(window_width * scale)
            new_height = int(window_height * scale)
            combined_frame = cv2.resize(combined_frame, (new_width, new_height))

        # نمایش پنجره ترکیبی
        cv2.imshow('Interactive Coloring', combined_frame)

        # خروج با کلید 'q'
        if cv2.waitKey(1) == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()