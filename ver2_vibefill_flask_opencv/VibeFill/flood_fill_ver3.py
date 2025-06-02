import cv2
import numpy as np
import mediapipe as mp
import os
import json
import time
import websocket
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import glob
from screeninfo import get_monitors  # اضافه کردن کتابخانه برای دریافت اطلاعات مانیتور

# تابع برای دریافت رزولوشن مانیتور اصلی
def get_monitor_resolution():
    try:
        monitor = get_monitors()[0]  # مانیتور اصلی
        return monitor.width, monitor.height
    except Exception as e:
        print(f"Error getting monitor resolution: {e}")
        return 1920, 1080  # رزولوشن پیش‌فرض (FHD)

# تنظیمات اولیه
cam_width, cam_height = 640, 480
monitor_width, monitor_height = get_monitor_resolution()  # دریافت رزولوشن مانیتور
max_window_width = int(monitor_width * 0.9)  # 90% عرض مانیتور
max_window_height = int(monitor_height * 0.9)  # 90% ارتفاع مانیتور
filter_size = 12
alpha = 0.4
pinch_threshold = 0.045
gesture_debounce = 0.5
animation_duration = 0.5
blur_intensity = 101
use_hardware_acceleration = True

# تنظیمات رنگ‌ها (بدون تغییر)
colors = {
    "red": {"rgb": (0, 0, 255), "name": "قرمز", "text_color": (255, 0, 0), "border_color": (255, 0, 0)},
    "green": {"rgb": (0, 255, 0), "name": "سبز", "text_color": (0, 255, 0), "border_color": (0, 255, 0)},
    "blue": {"rgb": (255, 0, 0), "name": "آبی", "text_color": (0, 0, 255), "border_color": (0, 0, 255)},
    "yellow": {"rgb": (0, 255, 255), "name": "زرد", "text_color": (255, 255, 0), "border_color": (255, 255, 0)},
    "orange": {"rgb": (0, 165, 255), "name": "نارنجی", "text_color": (255, 165, 0), "border_color": (255, 165, 0)},
    "crimson": {"rgb": (0, 0, 128), "name": "زرشکی", "text_color": (128, 0, 0), "border_color": (128, 0, 0)},
    "purple": {"rgb": (128, 0, 128), "name": "بنفش", "text_color": (128, 0, 128), "border_color": (128, 0, 128)},
    "brown": {"rgb": (42, 42, 165), "name": "قهوه‌ای", "text_color": (165, 42, 42), "border_color": (165, 42, 42)},
    "pink": {"rgb": (255, 192, 203), "name": "صورتی", "text_color": (255, 192, 203), "border_color": (255, 192, 203)},
    "cyan": {"rgb": (255, 255, 0), "name": "فیروزه‌ای", "text_color": (0, 255, 255), "border_color": (0, 255, 255)},
    "magenta": {"rgb": (255, 0, 255), "name": "سرخابی", "text_color": (255, 0, 255), "border_color": (255, 0, 255)},
    "white": {"rgb": (255, 255, 255), "name": "سفید", "text_color": (255, 255, 255), "border_color": (255, 255, 255)},
    "gray": {"rgb": (128, 128, 128), "name": "خاکستری", "text_color": (128, 128, 128), "border_color": (128, 128, 128)},
    "light_blue": {"rgb": (0, 191, 255), "name": "آبی روشن", "text_color": (0, 191, 255), "border_color": (0, 191, 255)},
    "dark_blue": {"rgb": (0, 0, 139), "name": "آبی تیره", "text_color": (0, 0, 139), "border_color": (0, 0, 139)},
    "light_green": {"rgb": (144, 238, 144), "name": "سبز روشن", "text_color": (144, 238, 144), "border_color": (144, 238, 144)},
    "dark_green": {"rgb": (0, 100, 0), "name": "سبز تیره", "text_color": (0, 100, 0), "border_color": (0, 100, 0)},
    "olive": {"rgb": (128, 128, 0), "name": "زیتونی", "text_color": (128, 128, 0), "border_color": (128, 128, 0)},
    "teal": {"rgb": (0, 128, 128), "name": "سبزآبی", "text_color": (0, 128, 128), "border_color": (0, 128, 128)},
    "violet": {"rgb": (238, 130, 238), "name": "بنفش روشن", "text_color": (238, 130, 238), "border_color": (238, 130, 238)},
    "gold": {"rgb": (0, 215, 255), "name": "طلایی", "text_color": (255, 215, 0), "border_color": (255, 215, 0)},
    "silver": {"rgb": (192, 192, 192), "name": "نقره‌ای", "text_color": (192, 192, 192), "border_color": (192, 192, 192)}
}

# تنظیمات عملیات (بدون تغییر)
operations = {
    "eraser": {"name": "پاکن", "text_color": (255, 255, 255), "border_color": (200, 0, 0)},
    "undo": {"name": "بازگشت", "text_color": (255, 140, 0), "border_color": (255, 140, 0)},
    "reset": {"name": "بازنشانی", "text_color": (128, 0, 128), "border_color": (128, 0, 128)},
    "next": {"name": "بعدی", "text_color": (0, 200, 200), "border_color": (0, 200, 200)},
    "prev": {"name": "قبلی", "text_color": (200, 200, 0), "border_color": (200, 200, 0)},
    "save": {"name": "ذخیره", "text_color": (255, 105, 180), "border_color": (255, 105, 180)}
}

# متغیرهای سراسری (بدون تغییر)
canvas = None
artwork_padded = None
initial_canvas = None
black_mask = None
undo_stack = []
finger_positions = []
ema_x, ema_y = None, None
selected_color = None
coloring_enabled = False
last_undo_time = 0
last_reset_time = 0
last_next_time = 0
last_prev_time = 0
last_save_time = 0
save_active = False
pinch_triggered = False
animation_states = {
    "color": {"start_time": 0, "last_color": None},
    "undo": {"start_time": 0},
    "reset": {"start_time": 0},
    "next": {"start_time": 0},
    "prev": {"start_time": 0},
    "save": {"start_time": 0}
}
current_image_index = 0
image_files = glob.glob("draw/*.png")

# تشخیص شتاب‌دهی سخت‌افزاری (بدون تغییر)
def detect_hardware_acceleration():
    if not use_hardware_acceleration:
        return "cpu"
    try:
        if cv2.cuda.getCudaEnabledDeviceCount() > 0:
            return "cuda"
        if cv2.ocl.haveOpenCL():
            cv2.ocl.setUseOpenCL(True)
            return "opencl"
        return "cpu"
    except Exception:
        return "cpu"

hardware_backend = detect_hardware_acceleration()

# تنظیمات Mediapipe (بدون تغییر)
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.75, min_tracking_confidence=0.75)

# تنظیمات WebSocket (بدون تغییر)
ws_url = "ws://services.irn9.chabokan.net:30068/ws"
ws = websocket.WebSocket()
try:
    ws.connect(ws_url)
except Exception as e:
    print(f"Error connecting to WebSocket: {e}")
    exit(1)

# تنظیمات دوربین (بدون تغییر)
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error opening camera. Please check camera connection.")
    exit(1)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, cam_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cam_height)

# بارگذاری فونت پارسی (بدون تغییر)
font_path = r"BNazanin.ttf"
try:
    font = ImageFont.truetype(font_path, 22)
except Exception as e:
    print(f"Error loading font {font_path}: {e}")
    font_path = r"BYekan_p30download.com.ttf"
    try:
        font = ImageFont.truetype(font_path, 22)
    except Exception as e:
        raise ValueError(f"No valid Persian font found: {e}")

# کش اندازه متن (بدون تغییر)
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

# محاسبه پیشرفت انیمیشن (بدون تغییر)
def get_animation_progress(start_time, duration):
    elapsed = time.time() - start_time
    return min(elapsed / duration, 1.0)

# رسم متن پارسی با انیمیشن (بدون تغییر)
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
        print(f"Error rendering Persian text: {e}")

# پیش‌پردازش پیشرفته تصویر دوربین (بدون تغییر)
def preprocess_camera_image(image, hardware_backend):
    try:
        if hardware_backend == "cuda":
            gpu_image = cv2.cuda_GpuMat()
            gpu_image.upload(image)
            clahe = cv2.cuda.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            gpu_lab = cv2.cuda.cvtColor(gpu_image, cv2.COLOR_BGR2LAB)
            gpu_l, gpu_a, gpu_b = cv2.cuda.split(gpu_lab)
            gpu_l_clahe = clahe.apply(gpu_l)
            gpu_lab_clahe = cv2.cuda.merge((gpu_l_clahe, gpu_a, gpu_b))
            gpu_enhanced = cv2.cuda.cvtColor(gpu_lab_clahe, cv2.COLOR_LAB2BGR)
            gamma = 1.2
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            gpu_table = cv2.cuda_LUT(gpu_enhanced, table)
            gpu_denoised = cv2.cuda.bilateralFilter(gpu_table, d=9, sigmaColor=75, sigmaSpace=75)
            enhanced_image = gpu_denoised.download()
        elif hardware_backend == "opencl":
            umat_image = cv2.UMat(image)
            lab = cv2.cvtColor(umat_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l_clahe = clahe.apply(l)
            lab_clahe = cv2.merge((l_clahe, a, b))
            enhanced = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
            gamma = 1.2
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            gamma_corrected = cv2.LUT(enhanced, table)
            denoised = cv2.bilateralFilter(gamma_corrected, d=9, sigmaColor=75, sigmaSpace=75)
            enhanced_image = cv2.UMat.get(denoised)
        else:
            input_image = image
            lab = cv2.cvtColor(input_image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l_clahe = clahe.apply(l)
            lab_clahe = cv2.merge((l_clahe, a, b))
            enhanced = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
            gamma = 1.2
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            gamma_corrected = cv2.LUT(enhanced, table)
            enhanced_image = cv2.bilateralFilter(gamma_corrected, d=9, sigmaColor=75, sigmaSpace=75)
        return enhanced_image
    except Exception as e:
        print(f"Error in camera image preprocessing: {e}")
        return image

# پیش‌پردازش تصویر (بدون تغییر)
def preprocess_image(image):
    try:
        denoised = cv2.bilateralFilter(image, d=9, sigmaColor=75, sigmaSpace=75)
        gaussian_blur = cv2.GaussianBlur(denoised, (5, 5), 0)
        sharpened = cv2.addWeighted(denoised, 1.5, gaussian_blur, -0.5, 0)
        lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l_clahe = clahe.apply(l)
        lab_clahe = cv2.merge((l_clahe, a, b))
        enhanced = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
        hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = np.clip(s * 1.2, 0, 255).astype(np.uint8)
        hsv_enhanced = cv2.merge((h, s, v))
        color_enhanced = cv2.cvtColor(hsv_enhanced, cv2.COLOR_HSV2BGR)
        gamma = 1.2
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
        gamma_corrected = cv2.LUT(color_enhanced, table)
        return gamma_corrected
    except Exception as e:
        print(f"Error in image preprocessing: {e}")
        return image

# بارگذاری تصویر با پدینگ 150 پیکسل (بدون تغییر)
def load_image(index):
    global canvas, artwork_padded, initial_canvas, black_mask
    try:
        if 0 <= index < len(image_files):
            image_path = image_files[index]
            canvas = cv2.imread(image_path)
            if canvas is None:
                raise ValueError(f"Failed to load image: {image_path}")
            canvas = preprocess_image(canvas)
            canvas = cv2.resize(canvas, (600, 450))
            artwork_padded = cv2.copyMakeBorder(
                canvas,
                150, 150, 150, 150,
                cv2.BORDER_CONSTANT,
                value=(255, 255, 255)
            )
            initial_canvas = artwork_padded.copy()
            canvas = artwork_padded.copy()
            gray = cv2.cvtColor(artwork_padded, cv2.COLOR_BGR2GRAY)
            _, black_mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
            black_mask = (black_mask == 255).astype(np.uint8) * 255
            undo_stack.clear()
            return True
        return False
    except Exception as e:
        print(f"Error loading image: {e}")
        return False

# ذخیره تصویر (بدون تغییر)
def save_image():
    global save_active, last_save_time
    try:
        if artwork_padded is None:
            raise ValueError("No image available to save")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join("static", "gallery", f"saved_{timestamp}.png")
        os.makedirs(os.path.join("static", "gallery"), exist_ok=True)
        cv2.imwrite(save_path, artwork_padded)
        print(f"Image saved to {save_path}")
        save_active = True
        last_save_time = time.time()
        animation_states["save"]["start_time"] = last_save_time
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False

# بارگذاری تصویر اولیه
if not load_image(current_image_index):
    print("Error: No images found to load")
    cap.release()
    cv2.destroyAllWindows()
    exit(1)

# حلقه اصلی
cv2.namedWindow('Interactive Coloring', cv2.WINDOW_NORMAL)  # تنظیم پنجره به حالت قابل تغییر اندازه
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        print("Error capturing frame from camera")
        break

    # پیش‌پردازش تصویر دوربین
    frame = preprocess_camera_image(frame, hardware_backend)
    frame = cv2.flip(frame, 1)
    frame = cv2.resize(frame, (cam_width, cam_height))
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    hands_results = hands.process(rgb_frame)
    x_avg, y_avg = None, None
    undo_active = False
    reset_active = False
    next_active = False
    prev_active = False
    save_active = False
    current_time = time.time()
    pinch_active = False
    is_left_hand_detected = False

    # کپی فریم برای رسم نقاط لندمارک
    landmark_frame = np.zeros_like(frame)

    # پردازش تشخیص دست
    if hands_results.multi_hand_landmarks and hands_results.multi_handedness:
        for hand_landmarks, handedness in zip(hands_results.multi_hand_landmarks, hands_results.multi_handedness):
            if handedness.classification[0].label == "Left":
                is_left_hand_detected = True
                continue

            mp_drawing.draw_landmarks(landmark_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            index_finger_tip = hand_landmarks.landmark[8]
            thumb_tip = hand_landmarks.landmark[4]
            h, w, _ = frame.shape
            x_index, y_index = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
            x_thumb, y_thumb = int(thumb_tip.x * w), int(thumb_tip.y * h)

            pinch_distance = np.sqrt((x_index - x_thumb) ** 2 + (y_index - y_thumb) ** 2) / w
            pinch_active = pinch_distance < pinch_threshold

            finger_positions.append((x_index, y_index))
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

    # اعمال تاری یا وضوح بر اساس تشخیص دست چپ
    if is_left_hand_detected:
        final_frame = frame.copy()
    else:
        blurred_frame = cv2.GaussianBlur(frame, (blur_intensity, blur_intensity), 0)
        final_frame = blurred_frame.copy()
        mask = landmark_frame > 0
        final_frame[mask] = landmark_frame[mask]

    # پردازش پیام‌های WebSocket
    try:
        ws.settimeout(0.01)
        message = ws.recv()
        if message:
            data = json.loads(message)
            if 'color' in data:
                color_name = data['color'].lower()
                if color_name in colors:
                    selected_color = colors[color_name]["rgb"]
                    coloring_enabled = True
                    animation_states["color"]["start_time"] = current_time
                    animation_states["color"]["last_color"] = selected_color
            elif 'action' in data:
                action = data['action'].lower()
                if action == "eraser":
                    selected_color = "eraser"
                    coloring_enabled = True
                    animation_states["color"]["start_time"] = current_time
                    animation_states["color"]["last_color"] = "eraser"
                elif action == "undo" and current_time - last_undo_time > gesture_debounce:
                    if undo_stack:
                        canvas = undo_stack.pop()
                        artwork_padded = canvas.copy()
                        undo_active = True
                        last_undo_time = current_time
                        animation_states["undo"]["start_time"] = current_time
                elif action == "reset_changes" and current_time - last_reset_time > gesture_debounce:
                    canvas = initial_canvas.copy()
                    artwork_padded = canvas.copy()
                    undo_stack.clear()
                    reset_active = True
                    last_reset_time = current_time
                    animation_states["reset"]["start_time"] = current_time
                elif action == "next_design" and current_time - last_next_time > gesture_debounce:
                    if current_image_index < len(image_files) - 1:
                        current_image_index += 1
                        if load_image(current_image_index):
                            next_active = True
                            last_next_time = current_time
                            animation_states["next"]["start_time"] = current_time
                elif action == "previous_design" and current_time - last_prev_time > gesture_debounce:
                    if current_image_index > 0:
                        current_image_index -= 1
                        if load_image(current_image_index):
                            prev_active = True
                            last_prev_time = current_time
                            animation_states["prev"]["start_time"] = current_time
                elif action == "save_painting" and current_time - last_save_time > gesture_debounce:
                    if save_image():
                        save_active = True
                        last_save_time = current_time
                        animation_states["save"]["start_time"] = current_time
    except Exception:
        pass

    if artwork_padded is None:
        print("Error: No image loaded. Stopping program.")
        break
    artwork_display = artwork_padded.copy()

    # پردازش ژست pinch برای دست راست
    if hands_results.multi_hand_landmarks and x_avg is not None and not is_left_hand_detected:
        x_art = int(x_avg * (artwork_padded.shape[1] / w))
        y_art = int(y_avg * (artwork_padded.shape[0] / h))
        cv2.circle(artwork_display, (x_art, y_art), 5, (0, 0, 255), -1)

        if pinch_active and not pinch_triggered and coloring_enabled:
            pinch_triggered = True
            if 0 <= x_art < canvas.shape[1] and 0 <= y_art < canvas.shape[0]:
                if black_mask[y_art, x_art] == 0:
                    if len(undo_stack) > 10:
                        undo_stack = undo_stack[-10:]
                    undo_stack.append(canvas.copy())
                    mask = np.zeros((canvas.shape[0] + 2, canvas.shape[1] + 2), dtype=np.uint8)
                    mask[1:-1, 1:-1] = black_mask
                    if selected_color == "eraser":
                        cv2.floodFill(
                            canvas,
                            mask,
                            (x_art, y_art),
                            (255, 255, 255),
                            loDiff=(50, 50, 50),
                            upDiff=(50, 50, 50),
                            flags=cv2.FLOODFILL_FIXED_RANGE
                        )
                        region = (mask[1:-1, 1:-1] > 0)
                        canvas[region] = initial_canvas[region]
                    else:
                        fill_color = selected_color
                        cv2.floodFill(
                            canvas,
                            mask,
                            (x_art, y_art),
                            fill_color,
                            loDiff=(50, 50, 50),
                            upDiff=(50, 50, 50),
                            flags=cv2.FLOODFILL_FIXED_RANGE
                        )
                    artwork_padded = canvas.copy()
        elif not pinch_active:
            pinch_triggered = False

    text_x = cam_width - 120
    if selected_color:
        if selected_color == "eraser":
            color_info = operations["eraser"]
            color_name = color_info["name"]
            text_color = color_info["text_color"]
            border_color = color_info["border_color"]
        else:
            color_info = next((info for info in colors.values() if info["rgb"] == selected_color), None)
            if color_info:
                color_name = color_info["name"]
                text_color = color_info["text_color"]
                border_color = color_info["border_color"]
            else:
                color_name, text_color, border_color = None, None, None
        if color_name:
            anim_progress = get_animation_progress(animation_states["color"]["start_time"], animation_duration)
            draw_persian_text_pil(
                final_frame,
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
            final_frame,
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
            final_frame,
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
            final_frame,
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
            final_frame,
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
            final_frame,
            operations["save"]["name"],
            (text_x, 225),
            font,
            text_color=operations["save"]["text_color"],
            border_color=operations["save"]["border_color"],
            anim_progress=anim_progress
        )

    # تنظیم پویا اندازه تصویر ترکیبی
    frame_resized = cv2.resize(final_frame, (cam_width, artwork_display.shape[0]))
    combined_frame = np.hstack((frame_resized, artwork_display))

    # مقیاس‌بندی تصویر برای تناسب با رزولوشن مانیتور
    window_width = combined_frame.shape[1]
    window_height = combined_frame.shape[0]
    if window_width > max_window_width or window_height > max_window_height:
        scale = min(max_window_width / window_width, max_window_height / window_height)
        new_width = int(window_width * scale)
        new_height = int(window_height * scale)
        combined_frame = cv2.resize(combined_frame, (new_width, new_height))
    else:
        new_width, new_height = window_width, window_height

    # تنظیم اندازه پنجره OpenCV
    cv2.resizeWindow('Interactive Coloring', new_width, new_height)
    cv2.imshow('Interactive Coloring', combined_frame)

    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    elif key == ord('w'):
        blur_intensity = min(blur_intensity + 2, 101)
        print(f"Blur intensity: {blur_intensity}")
    elif key == ord('s'):
        blur_intensity = max(blur_intensity - 2, 1)
        print(f"Blur intensity: {blur_intensity}")

cap.release()
cv2.destroyAllWindows()
ws.close()
hands.close()