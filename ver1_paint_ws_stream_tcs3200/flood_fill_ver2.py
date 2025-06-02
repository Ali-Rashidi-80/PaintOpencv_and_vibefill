import cv2
import numpy as np
import mediapipe as mp
from screeninfo import get_monitors
from bidi.algorithm import get_display
import arabic_reshaper
from PIL import Image, ImageDraw, ImageFont
import time
import os
import gc

# دریافت رزولوشن صفحه نمایش
try:
    monitor = get_monitors()[0]
    screen_width, screen_height = monitor.width, monitor.height
except Exception as e:
    print(f"خطا در دریافت رزولوشن صفحه: {e}")
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
except Exception as e:
    raise ValueError(f"فایل فونت B Yekan یافت نشد یا بارگذاری نشد: {e}")

# تنظیم مسیر پوشه draw و saved
draw_folder = r"C:\0\Accessible\WORK\machineVision\paint ver5\draw"
save_folder = os.path.join(draw_folder, "saved")
image_files = []
try:
    if not os.path.exists(draw_folder):
        raise FileNotFoundError(f"پوشه {draw_folder} یافت نشد.")
    image_files = sorted([f for f in os.listdir(draw_folder) if f.endswith('.png')],
                         key=lambda x: int(os.path.splitext(x)[0]))
    print(f"فایل‌های یافت‌شده: {image_files}")
    if not image_files:
        raise ValueError(f"هیچ فایل PNG در پوشه {draw_folder} یافت نشد.")
    # ایجاد پوشه saved اگر وجود نداشته باشد
    os.makedirs(save_folder, exist_ok=True)
except Exception as e:
    raise ValueError(f"خطا در بارگذاری تصاویر یا تنظیم پوشه ذخیره: {e}")

# متغیرهای جهانی
current_image_index = 0
artwork_width, artwork_height = 600, 450
padding = 150
canvas = None
artwork_padded = None
black_mask = None
initial_canvas = None
undo_stack = []
selected_color = None
coloring_enabled = False
finger_positions = []
filter_size = 12
pinch_threshold = 0.045
ema_x, ema_y = None, None
alpha = 0.3
undo_active = False
reset_active = False
next_active = False
prev_active = False
save_active = False
last_undo_time = 0
last_reset_time = 0
last_next_time = 0
last_prev_time = 0
last_save_time = 0
gesture_debounce = 0.5

# متغیرهای انیمیشن
animation_states = {
    "color": {"start_time": 0, "progress": 0, "last_color": None},
    "undo": {"start_time": 0, "progress": 0},
    "reset": {"start_time": 0, "progress": 0},
    "next": {"start_time": 0, "progress": 0},
    "prev": {"start_time": 0, "progress": 0},
    "save": {"start_time": 0, "progress": 0}
}
animation_duration = 0.3

def load_image(index):
    """بارگذاری و آماده‌سازی تصویر با محافظت از رنگ‌های مشکی"""
    global canvas, artwork_padded, black_mask, initial_canvas, undo_stack
    try:
        artwork_path = os.path.join(draw_folder, image_files[index])
        print(f"بارگذاری فایل: {artwork_path}")
        artwork = cv2.imread(artwork_path)
        if artwork is None:
            raise ValueError(f"تصویر {artwork_path} خوانده نشد.")
        
        # بررسی اندازه تصویر برای جلوگیری از مصرف زیاد حافظه
        if artwork.shape[0] * artwork.shape[1] > 2000 * 2000:
            raise ValueError(f"تصویر {artwork_path} بیش از حد بزرگ است.")
        
        # تغییر اندازه تصویر
        artwork = cv2.resize(artwork, (artwork_width, artwork_height))
        
        # افزودن پدینگ
        artwork_padded = cv2.copyMakeBorder(artwork, padding, padding, padding, padding,
                                            cv2.BORDER_CONSTANT, value=(255, 255, 255))
        canvas = artwork_padded.copy()
        
        # ایجاد ماسک برای نواحی مشکی
        gray = cv2.cvtColor(artwork_padded, cv2.COLOR_BGR2GRAY)
        _, black_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)
        
        # آماده‌سازی برای undo و ریست
        initial_canvas = canvas.copy()
        undo_stack.clear()
        
        # آزادسازی حافظه
        del artwork
        gc.collect()
        
        return True
    except Exception as e:
        print(f"خطا در بارگذاری تصویر {index + 1}: {e}")
        return False

def save_image():
    """ذخیره تصویر رنگ‌شده در پوشه saved"""
    global save_active, last_save_time
    try:
        if artwork_padded is None:
            raise ValueError("تصویر برای ذخیره موجود نیست.")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(save_folder, f"saved_{timestamp}.png")
        cv2.imwrite(save_path, artwork_padded)
        print(f"تصویر در {save_path} ذخیره شد.")
        save_active = True
        last_save_time = time.time()
        animation_states["save"]["start_time"] = last_save_time
        return True
    except Exception as e:
        print(f"خطا در ذخیره تصویر: {e}")
        return False

# بارگذاری تصویر اولیه
if not load_image(current_image_index):
    raise ValueError("بارگذاری تصویر اولیه ناموفق بود. لطفاً بررسی کنید که فایل‌های PNG با نام‌های عددی (مثل 1.png) در پوشه draw وجود دارند.")

# تنظیمات دوربین
try:
    cap = cv2.VideoCapture(0)
    cam_width, cam_height = 550, 300
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)
    cap.set(cv2.CAP_PROP_FPS, 30)
except Exception as e:
    raise ValueError(f"خطا در تنظیمات دوربین: {e}")

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
    "reset": {"name": "ریست", "text_color": (128, 0, 128), "border_color": (128, 0, 128)},
    "next": {"name": "تصویر بعدی", "text_color": (0, 200, 200), "border_color": (0, 200, 200)},
    "prev": {"name": "تصویر قبلی", "text_color": (200, 200, 0), "border_color": (200, 200, 0)},
    "save": {"name": "ذخیره تصویر", "text_color": (255, 105, 180), "border_color": (255, 105, 180)}
}

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
    try:
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_image, 'RGBA')
        
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        text_w, text_h = get_text_size(text, font)
        text_x, text_y = position

        alpha = int(255 * anim_progress)
        scale = 1.0 + 0.2 * (1.0 - anim_progress)
        bg_alpha = int(128 * anim_progress)

        if border_color:
            start_border_color = (100, 100, 100)
            border_color = tuple(
                int(start_border_color[i] + (border_color[i] - start_border_color[i]) * anim_progress)
                for i in range(3)
            ) + (alpha,)

        margin = 10
        scaled_w = text_w * scale
        scaled_h = text_h * scale
        offset_x = (scaled_w - text_w) / 2
        offset_y = (scaled_h - text_h) / 2

        draw.rounded_rectangle(
            (text_x-margin-offset_x, text_y-margin-offset_y, text_x+text_w+margin+offset_x, text_y+text_h+margin+offset_y),
            radius=5,
            fill=(bg_color[0], bg_color[1], bg_color[2], bg_alpha)
        )
        
        if border_color:
            draw.rounded_rectangle(
                (text_x-margin-offset_x, text_y-margin-offset_y, text_x+text_w+margin+offset_x, text_y+text_h+margin+offset_y),
                radius=5,
                outline=border_color,
                width=1
            )

        draw.text((text_x, text_y), bidi_text, font=font, fill=(text_color[0], text_color[1], text_color[2], alpha))
        image[:] = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"خطا در نمایش متن فارسی: {e}")

# تنظیمات Mediapipe برای بهبود تشخیص در نور کم
hands = mp_hands.Hands(min_detection_confidence=0.75, min_tracking_confidence=0.75, max_num_hands=2)

# حلقه اصلی
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("خطا در دریافت فریم از دوربین. لطفاً اتصال دوربین را بررسی کنید.")
        break

    # تنظیم روشنایی فریم برای بهبود تشخیص
    frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=10)
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (cam_width, cam_height))
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # تشخیص دست و لندمارک‌ها
    hands_results = hands.process(rgb_frame)
    x_avg, y_avg = None, None
    undo_active = False
    reset_active = False
    next_active = False
    prev_active = False
    save_active = False
    current_time = time.time()

    # پردازش دست‌ها
    if hands_results.multi_hand_landmarks and hands_results.multi_handedness:
        for hand_landmarks, handedness in zip(hands_results.multi_hand_landmarks, hands_results.multi_handedness):
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            index_finger_tip = hand_landmarks.landmark[8]
            h, w, _ = frame.shape
            x, y = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
            
            finger_positions.append((x, y))
            if len(finger_positions) > filter_size:
                finger_positions.pop(0)
            
            x_mean = np.mean([pos[0] for pos in finger_positions])
            y_mean = np.mean([pos[1] for pos in finger_positions])

            if ema_x is None or ema_y is None:
                ema_x, ema_y = x_mean, y_mean
            else:
                ema_x = alpha * x_mean + (1 - alpha) * ema_x
                ema_y = alpha * y_mean + (1 - alpha) * ema_y
            
            x_avg, y_avg = int(ema_x), int(ema_y)

            # بررسی دست چپ
            is_left_hand = handedness.classification[0].label == "Left"

            # عملیات دست چپ
            if is_left_hand:
                # تصویر بعدی (شست و اشاره)
                if detect_pinch(hand_landmarks, 4, 8) and current_time - last_next_time > gesture_debounce:
                    if current_image_index < len(image_files) - 1:
                        current_image_index += 1
                        if load_image(current_image_index):
                            next_active = True
                            last_next_time = current_time
                            animation_states["next"]["start_time"] = current_time
                
                # تصویر قبلی (شست و وسط)
                if detect_pinch(hand_landmarks, 4, 12) and current_time - last_prev_time > gesture_debounce:
                    if current_image_index > 0:
                        current_image_index -= 1
                        if load_image(current_image_index):
                            prev_active = True
                            last_prev_time = current_time
                            animation_states["prev"]["start_time"] = current_time
                
                # ذخیره تصویر (شست و کوچک)
                if detect_pinch(hand_landmarks, 4, 20) and current_time - last_save_time > gesture_debounce:
                    if save_image():
                        save_active = True
                        last_save_time = current_time
                        animation_states["save"]["start_time"] = current_time

            # عملیات عمومی (برای هر دو دست)
            if 0 <= x_avg < cam_width and y_avg < color_bar_height:
                new_color = tuple(map(int, color_bar[0, x_avg]))
                if new_color != animation_states["color"]["last_color"]:
                    animation_states["color"]["start_time"] = current_time
                    animation_states["color"]["last_color"] = new_color
                selected_color = new_color

            if detect_pinch(hand_landmarks, 4, 8):
                coloring_enabled = True
            else:
                coloring_enabled = False

            if detect_pinch(hand_landmarks, 4, 20) and not is_left_hand and current_time - last_undo_time > gesture_debounce:
                undo_active = True
                last_undo_time = current_time
                animation_states["undo"]["start_time"] = current_time
                if undo_stack:
                    canvas = undo_stack.pop()
                    artwork_padded = canvas.copy()

            if detect_pinch(hand_landmarks, 4, 12) and not is_left_hand and current_time - last_reset_time > gesture_debounce:
                reset_active = True
                last_reset_time = current_time
                animation_states["reset"]["start_time"] = current_time
                canvas = initial_canvas.copy()
                artwork_padded = canvas.copy()
                undo_stack.clear()

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
            if next_active:
                anim_progress = get_animation_progress(animation_states["next"]["start_time"], animation_duration)
                draw_persian_text_pil(
                    frame,
                    operations["next"]["name"],
                    (text_x, 155),
                    font,
                    text_color=operations["next"]["text_color"],
                    border_color=operations["next"]["border_color"],
                    anim_progress=anim_progress
                )
            if prev_active:
                anim_progress = get_animation_progress(animation_states["prev"]["start_time"], animation_duration)
                draw_persian_text_pil(
                    frame,
                    operations["prev"]["name"],
                    (text_x, 190),
                    font,
                    text_color=operations["prev"]["text_color"],
                    border_color=operations["prev"]["border_color"],
                    anim_progress=anim_progress
                )
            if save_active:
                anim_progress = get_animation_progress(animation_states["save"]["start_time"], animation_duration)
                draw_persian_text_pil(
                    frame,
                    operations["save"]["name"],
                    (text_x, 225),
                    font,
                    text_color=operations["save"]["text_color"],
                    border_color=operations["save"]["border_color"],
                    anim_progress=anim_progress
                )

    frame_with_bar = np.vstack((color_bar, frame))
    
    # بررسی وجود artwork_padded
    if artwork_padded is None:
        print("خطا: تصویر بارگذاری نشده است. برنامه متوقف می‌شود.")
        break
    artwork_display = artwork_padded.copy()
    
    if hands_results.multi_hand_landmarks and x_avg is not None:
        x_art = int(x_avg * (artwork_padded.shape[1] / w))
        y_art = int(y_avg * (artwork_padded.shape[0] / h))
        cv2.circle(artwork_display, (x_art, y_art), 5, (0, 0, 255), -1)

        if coloring_enabled and selected_color:
            if 0 <= x_art < canvas.shape[1] and 0 <= y_art < canvas.shape[0]:
                if black_mask[y_art, x_art] == 0:
                    # محدود کردن undo_stack برای مدیریت حافظه
                    if len(undo_stack) > 10:
                        undo_stack = undo_stack[-10:]
                    undo_stack.append(canvas.copy())
                    mask = np.zeros((canvas.shape[0] + 2, canvas.shape[1] + 2), dtype=np.uint8)
                    mask[1:-1, 1:-1] = black_mask
                    fill_color = (255, 255, 255) if selected_color == (0, 0, 0) else selected_color
                    try:
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
                    except Exception as e:
                        print(f"خطا در رنگ‌آمیزی: {e}")

    frame_with_bar = cv2.resize(frame_with_bar, (cam_width, artwork_display.shape[0]))
    combined_frame = np.hstack((frame_with_bar, artwork_display))

    window_width = combined_frame.shape[1]
    window_height = combined_frame.shape[0]
    if window_width > max_window_width or window_height > max_window_height:
        scale = min(max_window_width / window_width, max_window_height / window_height)
        new_width = int(window_width * scale)
        new_height = int(window_height * scale)
        combined_frame = cv2.resize(combined_frame, (new_width, new_height))

    cv2.imshow('Interactive Coloring', combined_frame)
    if cv2.waitKey(1) == ord('q'):
        break

# آزادسازی منابع
cap.release()
cv2.destroyAllWindows()
hands.close()
gc.collect()