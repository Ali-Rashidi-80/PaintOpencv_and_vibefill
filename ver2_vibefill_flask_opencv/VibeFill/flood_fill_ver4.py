import sys
import cv2
import numpy as np
import mediapipe as mp
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QTabWidget, QGridLayout,
                             QScrollArea, QDialog, QDialogButtonBox, QTextEdit)
from PyQt6.QtGui import QImage, QPixmap, QFont, QColor, QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PIL import Image, ImageDraw, ImageFont
import glob
import time
import os
import platform
import threading
from queue import Queue
import uuid
try:
    from persiantools.jdatetime import JalaliDateTime
    PERSIANTOOLS_AVAILABLE = True
except ImportError:
    PERSIANTOOLS_AVAILABLE = False
if platform.system() == "Windows":
    import arabic_reshaper
    from bidi.algorithm import get_display

# Desktop resolutions
RESOLUTIONS = {
    'final_width': 1072,
    'final_height': 603,
    'cam_width': 536,
    'cam_height': 301,
    'canvas_width': 536,
    'canvas_height': 301,
    'padding': 100
}

# Blur settings
BLUR_AMOUNT = 81
DEFAULT_BLUR = True

# Color definitions
COLORS = {
    "red": {"rgb": (255, 0, 0), "name": "قرمز", "text_color": (255, 0, 0), "border_color": (255, 0, 0)},
    "green": {"rgb": (0, 255, 0), "name": "سبز", "text_color": (0, 255, 0), "border_color": (0, 255, 0)},
    "blue": {"rgb": (0, 0, 255), "name": "آبی", "text_color": (0, 0, 255), "border_color": (0, 0, 255)},
    "yellow": {"rgb": (255, 255, 0), "name": "زرد", "text_color": (255, 255, 0), "border_color": (255, 255, 0)},
    "orange": {"rgb": (255, 165, 0), "name": "نارنجی", "text_color": (255, 165, 0), "border_color": (255, 165, 0)},
    "crimson": {"rgb": (128, 0, 0), "name": "زرشکی", "text_color": (128, 0, 0), "border_color": (128, 0, 0)},
    "purple": {"rgb": (128, 0, 128), "name": "بنفش", "text_color": (128, 0, 128), "border_color": (128, 0, 128)},
    "brown": {"rgb": (165, 42, 42), "name": "قهوه‌ای", "text_color": (165, 42, 42), "border_color": (165, 42, 42)},
    "pink": {"rgb": (255, 192, 203), "name": "صورتی", "text_color": (255, 192, 203), "border_color": (255, 192, 203)},
    "cyan": {"rgb": (0, 255, 255), "name": "فیروزه‌ای", "text_color": (0, 255, 255), "border_color": (0, 255, 255)},
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
    "gold": {"rgb": (255, 215, 0), "name": "طلایی", "text_color": (255, 215, 0), "border_color": (255, 215, 0)},
    "silver": {"rgb": (192, 192, 192), "name": "نقره‌ای", "text_color": (192, 192, 192), "border_color": (192, 192, 192)}
}

# Operation definitions
OPERATIONS = {
    "eraser": {"name": "پاکن", "text_color": (255, 255, 255), "border_color": (200, 0, 0)},
    "undo": {"name": "بازگشت", "text_color": (255, 140, 0), "border_color": (255, 140, 0)},
    "reset": {"name": "بازنشانی", "text_color": (128, 0, 128), "border_color": (128, 0, 128)},
    "next": {"name": "بعدی", "text_color": (0, 200, 200), "border_color": (0, 200, 200)},
    "prev": {"name": "قبلی", "text_color": (200, 200, 0), "border_color": (200, 200, 0)},
    "save": {"name": "ذخیره", "text_color": (255, 105, 180), "border_color": (255, 105, 180)}
}

# Mediapipe setup
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Preprocessing function for camera image
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
            enhanced = cv2.cuda.cvtColor(gpu_lab_clahe, cv2.COLOR_LAB2BGR)
            gamma = 1.2
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            gamma_corrected = cv2.cuda_LUT(enhanced, table)
            denoised = cv2.cuda.bilateralFilter(gamma_corrected, d=9, sigmaColor=75, sigmaSpace=75)
            enhanced_image = denoised.download()
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
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
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
        print(f"Error in preprocess_camera_image ({hardware_backend}): {e}")
        return image

# Preprocessing function for loaded image
def preprocess_image(image):
    try:
        gaussian_blur = cv2.GaussianBlur(image, (5, 5), 0)
        enhanced = cv2.addWeighted(image, 1.2, gaussian_blur, -0.2, 0)
        return enhanced
    except Exception as e:
        print(f"Error in preprocess_image: {e}")
        return image

# Video processing thread
class VideoThread(QThread):
    frame_signal = pyqtSignal(tuple)

    def __init__(self):
        super().__init__()
        self.running = True
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Error: Could not open webcam")
        self.frame_queue = Queue(maxsize=30)
        self.processed_frame_queue = Queue(maxsize=30)
        self.hand_results_queue = Queue(maxsize=30)
        self.hardware_backend = "cpu"
        
        # Smart detection of hardware backend
        try:
            if cv2.cuda.getCudaEnabledDeviceCount() > 0:
                self.hardware_backend = "cuda"
                print("CUDA detected")
        except Exception:
            pass
        
        if self.hardware_backend == "cpu":
            try:
                if cv2.ocl.haveOpenCL():
                    cv2.ocl.setUseOpenCL(True)
                    self.hardware_backend = "opencl"
                    print("OpenCL detected")
            except Exception:
                pass
        
        if self.hardware_backend == "cpu":
            print("Using CPU backend")
        
        threading.Thread(target=self.preprocess_frame_worker, daemon=True).start()
        threading.Thread(target=self.hand_detection_worker, daemon=True).start()

    def preprocess_frame_worker(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1)
                if frame is None:
                    continue
                processed_frame = preprocess_camera_image(frame, self.hardware_backend)
                processed_frame = cv2.resize(processed_frame, (RESOLUTIONS['cam_width'], RESOLUTIONS['cam_height']))
                processed_frame = cv2.flip(processed_frame, 1)
                self.processed_frame_queue.put(processed_frame)
                self.frame_queue.task_done()
            except Exception:
                continue

    def hand_detection_worker(self):
        while self.running:
            try:
                frame = self.processed_frame_queue.get(timeout=1)
                if frame is None:
                    continue
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                hands_results = hands.process(rgb_frame)
                self.hand_results_queue.put((frame, hands_results))
                self.processed_frame_queue.task_done()
            except Exception:
                continue

    def run(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                frame = np.zeros((RESOLUTIONS['cam_height'], RESOLUTIONS['cam_width'], 3), dtype=np.uint8)
            try:
                self.frame_queue.put(frame, timeout=0.1)
                frame, hands_results = self.hand_results_queue.get(timeout=0.1)
                self.frame_signal.emit((frame, hands_results))
                self.hand_results_queue.task_done()
            except Exception:
                continue

    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()

# Image modal dialog
class ImageModal(QDialog):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        self.setWindowTitle("نمایش تصویر")
        self.setModal(True)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Image display
        pixmap = QPixmap(image_path).scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio)
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)

        # Buttons
        buttons = QDialogButtonBox()
        open_button = buttons.addButton("بازکردن", QDialogButtonBox.ButtonRole.AcceptRole)
        delete_button = buttons.addButton("حذف", QDialogButtonBox.ButtonRole.RejectRole)
        cancel_button = buttons.addButton("لغو", QDialogButtonBox.ButtonRole.RejectRole)
        open_button.clicked.connect(self.open_image)
        delete_button.clicked.connect(self.delete_image)
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def open_image(self):
        try:
            if platform.system() == "Windows":
                os.startfile(self.image_path)
            elif platform.system() == "Darwin":
                os.system(f"open {self.image_path}")
            else:
                os.system(f"xdg-open {self.image_path}")
            self.accept()
        except Exception as e:
            print(f"Error opening image: {e}")

    def delete_image(self):
        try:
            os.remove(self.image_path)
            self.accept()
        except Exception as e:
            print(f"Error deleting image: {e}")

# Main application window
class PaintingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("نقاشی دیجیتال آفلاین")
        self.setStyleSheet("""
            QMainWindow { background-color: #2c3e50; color: #ecf0f1; }
            QLabel { color: #ecf0f1; font-size: 16px; }
            QPushButton { 
                background-color: #4e73df; 
                color: white; 
                border-radius: 5px; 
                padding: 6px; 
                font-size: 14px; 
                min-width: 100px;
            }
            QPushButton:hover { background-color: #1cc88a; }
            QComboBox { 
                background-color: #34495e; 
                color: #ecf0f1; 
                border: 1px solid #4e73df; 
                padding: 4px; 
                font-size: 16px; 
                font-family: 'Arial'; 
                border-radius: 5px;
                min-width: 150px;
            }
            QComboBox QAbstractItemView { 
                background-color: #34495e; 
                color: #ecf0f1; 
                selection-background-color: #1cc88a; 
                font-size: 16px; 
                padding: 8px;
                border-radius: 5px;
            }
            QComboBox QAbstractItemView::item { 
                padding: 10px; 
                border-bottom: 1px solid #4e73df;
            }
            QTabWidget::pane { border: 1px solid #4e73df; background-color: #34495e; }
            QTabBar::tab { background: #4e73df; color: white; padding: 8px; }
            QTabBar::tab:selected { background: #1cc88a; }
            QScrollArea { background-color: #34495e; border: none; }
            QTextEdit { background-color: #34495e; color: #ecf0f1; border: 1px solid #4e73df; }
        """)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)

        # Initialize state
        self.canvas = None
        self.artwork_padded = None
        self.initial_canvas = None
        self.black_mask = None
        self.undo_stack = []
        self.finger_positions = []
        self.ema_x = None
        self.ema_y = None
        self.selected_color = None
        self.coloring_enabled = False
        self.last_action_time = {key: 0 for key in OPERATIONS}
        self.pinch_triggered = False
        self.current_text = None
        self.text_start_time = 0
        self.current_image_index = 0
        self.image_files = glob.glob("draw/*.png")
        try:
            self.font = ImageFont.truetype("BNazanin.ttf", 22)
        except Exception:
            print("Warning: BNazanin.ttf not found, trying fallback font")
            try:
                self.font = ImageFont.truetype("BYekan_p30download.com.ttf", 22)
            except Exception:
                print("Warning: No Persian font found, using default font")
                self.font = ImageFont.load_default()

        # Initialize video thread
        self.video_thread = VideoThread()
        self.video_thread.frame_signal.connect(self.update_frame)
        self.video_thread.start()

        # Setup UI
        self.setup_ui()
        if not self.load_image(self.current_image_index):
            print("Error: No images found to load")
            self.close()

        # Setup timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_display)
        self.timer.start(33)  # ~30 FPS

        # Show maximized
        self.showMaximized()

    def setup_ui(self):
        """Setup the main UI components."""
        main_widget = QWidget()
        main_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Tabs
        tabs = QTabWidget()
        tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        main_layout.addWidget(tabs)
        main_layout.setStretchFactor(tabs, 1)

        # Painting Tab
        painting_tab = QWidget()
        painting_layout = QVBoxLayout(painting_tab)
        painting_layout.setContentsMargins(0, 0, 0, 0)
        painting_layout.setSpacing(10)
        tabs.addTab(painting_tab, "نقاشی")

        # Display area
        display_widget = QWidget()
        display_layout = QHBoxLayout(display_widget)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(0)
        self.display_label = QLabel()
        self.display_label.setFixedSize(RESOLUTIONS['final_width'], RESOLUTIONS['final_height'])
        self.display_label.setStyleSheet("border: 1px solid #4e73df;")
        display_layout.addWidget(self.display_label)
        display_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        painting_layout.addWidget(display_widget)

        # Controls
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(20)
        controls_layout.addStretch(1)

        # Color selection
        color_layout = QVBoxLayout()
        color_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color_layout.setSpacing(5)
        self.color_combo = QComboBox()
        color_model = QStandardItemModel()
        for color_name, info in COLORS.items():
            item = QStandardItem(info["name"])
            item.setData(color_name, Qt.ItemDataRole.UserRole)
            item.setBackground(QColor(*info["text_color"]))
            item.setForeground(QColor(*info["text_color"]))
            color_model.appendRow(item)
        self.color_combo.setModel(color_model)
        color_select_button = QPushButton("انتخاب رنگ")
        color_select_button.clicked.connect(self.change_color)
        color_layout.addWidget(QLabel("انتخاب رنگ:"))
        color_layout.addWidget(self.color_combo)
        color_layout.addWidget(color_select_button)
        controls_layout.addLayout(color_layout)

        # Action selection
        action_layout = QVBoxLayout()
        action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_layout.setSpacing(5)
        self.action_combo = QComboBox()
        action_model = QStandardItemModel()
        for action, info in OPERATIONS.items():
            item = QStandardItem(info["name"])
            item.setData(action, Qt.ItemDataRole.UserRole)
            item.setBackground(QColor(*info["border_color"]))
            item.setForeground(QColor(255, 255, 255))
            action_model.appendRow(item)
        self.action_combo.setModel(action_model)
        action_select_button = QPushButton("اجرای اقدام")
        action_select_button.clicked.connect(lambda: self.perform_action(self.action_combo.currentData()))
        action_layout.addWidget(QLabel("انتخاب اقدام:"))
        action_layout.addWidget(self.action_combo)
        action_layout.addWidget(action_select_button)
        controls_layout.addLayout(action_layout)

        controls_layout.addStretch(1)
        painting_layout.addWidget(controls_widget)

        # Hardware backend label
        self.backend_label = QLabel(f"شتاب‌دهنده: {self.video_thread.hardware_backend}")
        self.backend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.backend_label.setStyleSheet("font-size: 12px; color: #ecf0f1;")
        painting_layout.addWidget(self.backend_label)

        painting_layout.addStretch(1)

        # Gallery Tab
        gallery_tab = QWidget()
        gallery_layout = QVBoxLayout(gallery_tab)
        gallery_layout.setContentsMargins(10, 10, 10, 10)
        gallery_layout.setSpacing(10)
        tabs.addTab(gallery_tab, "گالری")

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        gallery_widget = QWidget()
        self.gallery_grid = QGridLayout(gallery_widget)
        self.gallery_grid.setContentsMargins(0, 0, 0, 0)
        self.gallery_grid.setSpacing(10)
        scroll_area.setWidget(gallery_widget)
        gallery_layout.addWidget(scroll_area)

        self.load_gallery()

        # About Tab
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setContentsMargins(10, 10, 10, 10)
        about_layout.setSpacing(10)
        tabs.addTab(about_tab, "درباره")

        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        about_text.setHtml("""
            <h2 style='color: #ecf0f1; text-align: center;'>درباره نقاشی دیجیتال آفلاین</h2>
            <p style='color: #ecf0f1; font-size: 14px;'>
                این برنامه یک ابزار نقاشی دیجیتال آفلاین است که با استفاده از وب‌کم و تشخیص دست، امکان رنگ‌آمیزی تصاویر را فراهم می‌کند. ویژگی‌های کلیدی برنامه عبارتند از:
            </p>
            <ul style='color: #ecf0f1; font-size: 14px;'>
                <li><b>تشخیص دست:</b> استفاده از Mediapipe برای تشخیص حرکات دست راست و غیرفعال کردن بلور با دست چپ.</li>
                <li><b>نقاشی و پاک‌کن:</b> رنگ‌آمیزی مناطق با الگوریتم FloodFill و پاک کردن با بازگرداندن تصویر اولیه.</li>
                <li><b>شتاب‌دهی سخت‌افزاری:</b> پشتیبانی از CUDA و OpenCL برای پردازش سریع‌تر تصویر.</li>
                <li><b>پیش‌پردازش تصویر:</b> استفاده از CLAHE برای کاهش تأثیر نور خورشید روی تصویر وب‌کم.</li>
                <li><b>ذخیره و گالری:</b> ذخیره خودکار تصاویر در پوشه static/gallery و نمایش آن‌ها با تاریخ شمسی.</li>
                <li><b>رابط کاربری:</b> طراحی ریسپانسیو، راست‌به‌چپ، با انیمیشن‌های متنی و فونت پارسی.</li>
                <li><b>اقدامات:</b> پشتیبانی از بازگشت (Undo)، بازنشانی، تصویر بعدی/قبلی، و ذخیره.</li>
            </ul>
            <p style='color: #ecf0f1; font-size: 14px;'>
                این برنامه برای استفاده آفلاین طراحی شده و نیاز به اتصال اینترنت ندارد. تصاویر در پوشه draw بارگذاری شده و در گالری ذخیره می‌شوند.
            </p>
        """)
        about_layout.addWidget(about_text)

    def load_gallery(self):
        """Load images into the gallery grid with Persian or Gregorian date."""
        for i in range(self.gallery_grid.count()):
            self.gallery_grid.itemAt(i).widget().deleteLater()
        
        gallery_folder = os.path.join("static", "gallery")
        os.makedirs(gallery_folder, exist_ok=True)
        images = glob.glob(os.path.join(gallery_folder, "*.png"))
        images.sort(key=os.path.getctime, reverse=True)
        
        for i, img_path in enumerate(images):
            pixmap = QPixmap(img_path).scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio)
            image_label = QLabel()
            image_label.setPixmap(pixmap)
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setStyleSheet("border: 1px solid #4e73df; padding: 5px;")
            image_label.mousePressEvent = lambda event, path=img_path: self.show_image_modal(path)

            ctime = os.path.getctime(img_path)
            if PERSIANTOOLS_AVAILABLE:
                date_str = JalaliDateTime.fromtimestamp(ctime).strftime("%Y/%m/%d %H:%M")
            else:
                date_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(ctime))
            date_label = QLabel(date_str)
            date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            date_label.setStyleSheet("""
                background-color: #34495e; 
                color: #ecf0f1; 
                border: 1px solid #4e73df; 
                border-radius: 5px; 
                padding: 5px; 
                font-size: 12px;
            """)

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0	شکلات
            container_layout.setSpacing(5)
            container_layout.addWidget(image_label)
            container_layout.addWidget(date_label)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.gallery_grid.addWidget(container, i // 3, i % 3)

    def show_image_modal(self, image_path):
        """Show a modal dialog with the selected image."""
        modal = ImageModal(image_path, self)
        modal.exec()
        self.load_gallery()

    def load_image(self, index):
        """Load an image from the draw folder."""
        if 0 <= index < len(self.image_files):
            image_path = self.image_files[index]
            self.canvas = cv2.imread(image_path)
            if self.canvas is None:
                print(f"Error: Could not load image {image_path}")
                return False
            self.canvas = preprocess_image(self.canvas)
            self.canvas = cv2.resize(self.canvas, (RESOLUTIONS['canvas_width'], RESOLUTIONS['canvas_height']))
            self.artwork_padded = cv2.copyMakeBorder(
                self.canvas, RESOLUTIONS['padding'], RESOLUTIONS['padding'], RESOLUTIONS['padding'], RESOLUTIONS['padding'],
                cv2.BORDER_CONSTANT, value=(255, 255, 255)
            )
            self.initial_canvas = self.artwork_padded.copy()
            self.canvas = self.artwork_padded.copy()
            gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
            _, self.black_mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
            self.black_mask = (self.black_mask == 255).astype(np.uint8) * 255
            self.undo_stack.clear()
            return True
        return False

    def change_color(self):
        """Handle color selection."""
        color_name = self.color_combo.currentData()
        if color_name:
            self.selected_color = "eraser" if color_name == "eraser" else COLORS[color_name]["rgb"]
            self.coloring_enabled = True
            info = OPERATIONS["eraser"] if color_name == "eraser" else COLORS[color_name]
            self.current_text = f"رنگ: {info['name']}"
            self.text_start_time = time.time()

    def perform_action(self, action):
        """Handle action selection."""
        if not action:
            return
        current_time = time.time()
        if current_time - self.last_action_time[action] > 0.5:
            self.last_action_time[action] = current_time
            self.current_text = OPERATIONS[action]["name"]
            self.text_start_time = current_time
            if action == "undo" and self.undo_stack:
                self.canvas = self.undo_stack.pop()
                self.artwork_padded = self.canvas.copy()
            elif action == "reset":
                self.canvas = self.initial_canvas.copy()
                self.artwork_padded = self.canvas.copy()
                self.undo_stack.clear()
            elif action == "next" and self.current_image_index < len(self.image_files) - 1:
                self.current_image_index += 1
                self.load_image(self.current_image_index)
            elif action == "prev" and self.current_image_index > 0:
                self.current_image_index -= 1
                self.load_image(self.current_image_index)
            elif action == "save":
                gallery_folder = os.path.join("static", "gallery")
                os.makedirs(gallery_folder, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_name = f"saved_{timestamp}.png"
                file_path = os.path.join(gallery_folder, file_name)
                cv2.imwrite(file_path, self.artwork_padded)
                print(f"Image saved to {file_path}")
                self.load_gallery()

    def update_frame(self, data):
        """Process incoming video frames with accurate coordinate mapping and eraser logic."""
        frame, hands_results = data
        current_time = time.time()
        x_avg, y_avg = None, None
        pinch_active = False
        is_left_hand_detected = False

        # Initialize landmark frame
        landmark_frame = np.zeros_like(frame)
        if hands_results.multi_hand_landmarks and hands_results.multi_handedness:
            for hand_landmarks, handedness in zip(hands_results.multi_hand_landmarks, hands_results.multi_handedness):
                hand_label = handedness.classification[0].label
                if hand_label == "Left":
                    is_left_hand_detected = True
                    continue
                mp_drawing.draw_landmarks(landmark_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                index_finger_tip = hand_landmarks.landmark[8]
                thumb_tip = hand_landmarks.landmark[4]
                h, w = frame.shape[:2]
                x_index, y_index = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                x_thumb, y_thumb = int(thumb_tip.x * w), int(thumb_tip.y * h)
                
                pinch_distance = np.sqrt((x_index - x_thumb) ** 2 + (y_index - y_thumb) ** 2) / w
                pinch_active = pinch_distance < 0.045
                
                self.finger_positions.append((x_index, y_index))
                if len(self.finger_positions) > 15:
                    self.finger_positions.pop(0)
                x_mean = np.mean([pos[0] for pos in self.finger_positions])
                y_mean = np.mean([pos[1] for pos in self.finger_positions])
                self.ema_x = 0.4 * x_mean + (1 - 0.4) * (self.ema_x or x_mean)
                self.ema_y = 0.4 * y_mean + (1 - 0.4) * (self.ema_y or y_mean)
                x_avg, y_avg = int(self.ema_x), int(self.ema_y)

        # Apply blur based on left hand detection
        final_frame = cv2.GaussianBlur(frame, (BLUR_AMOUNT, BLUR_AMOUNT), 0) if DEFAULT_BLUR and not is_left_hand_detected else frame.copy()
        mask = landmark_frame > 0
        final_frame[mask] = landmark_frame[mask]

        # Initialize artwork display
        artwork_display = self.artwork_padded.copy() if self.artwork_padded is not None else np.zeros((RESOLUTIONS['canvas_height'] + 2 * RESOLUTIONS['padding'], RESOLUTIONS['canvas_width'] + 2 * RESOLUTIONS['padding'], 3), dtype=np.uint8)
        
        # Handle painting/eraser with corrected coordinates
        if x_avg is not None and not is_left_hand_detected and self.canvas is not None:
            # Map camera coordinates to padded artwork coordinates
            cam_w, cam_h = RESOLUTIONS['cam_width'], RESOLUTIONS['cam_height']
            art_w, art_h = RESOLUTIONS['canvas_width'] + 2 * RESOLUTIONS['padding'], RESOLUTIONS['canvas_height'] + 2 * RESOLUTIONS['padding']
            x_art = int(x_avg * (art_w / cam_w))
            y_art = int(y_avg * (art_h / cam_h))
            cv2.circle(artwork_display, (x_art, y_art), 5, (0, 0, 255), -1)
            
            if pinch_active and not self.pinch_triggered and self.coloring_enabled:
                self.pinch_triggered = True
                if 0 <= x_art < self.canvas.shape[1] and 0 <= y_art < self.canvas.shape[0]:
                    if self.black_mask[y_art, x_art] == 0:
                        if len(self.undo_stack) > 10:
                            self.undo_stack = self.undo_stack[-10:]
                        self.undo_stack.append(self.canvas.copy())
                        mask = np.zeros((self.canvas.shape[0] + 2, self.canvas.shape[1] + 2), dtype=np.uint8)
                        mask[1:-1, 1:-1] = self.black_mask
                        if self.selected_color == "eraser":
                            print(f"Erasing at ({x_art}, {y_art})")
                            cv2.floodFill(
                                self.canvas,
                                mask,
                                (x_art, y_art),
                                (255, 255, 255),
                                loDiff=(50, 50, 50),
                                upDiff=(50, 50, 50),
                                flags=cv2.FLOODFILL_FIXED_RANGE
                            )
                            region = (mask[1:-1, 1:-1] > 0)
                            print(f"Eraser region shape: {region.shape}")
                            self.canvas[region] = self.initial_canvas[region]
                        elif self.selected_color is not None:
                            fill_color = self.selected_color
                            cv2.floodFill(
                                self.canvas,
                                mask,
                                (x_art, y_art),
                                fill_color,
                                loDiff=(50, 50, 50),
                                upDiff=(50, 50, 50),
                                flags=cv2.FLOODFILL_FIXED_RANGE
                            )
                        self.artwork_padded = self.canvas.copy()
            elif not pinch_active:
                self.pinch_triggered = False

        # Render text on camera frame
        if self.current_text:
            progress = min((current_time - self.text_start_time) / 0.5, 1.0)
            text_color = (255, 255, 255)
            border_color = (200, 0, 0)
            if self.current_text.startswith("رنگ:"):
                color_name = self.current_text.replace("رنگ: ", "")
                for cname, info in COLORS.items():
                    if info["name"] == color_name:
                        text_color = info["text_color"]
                        border_color = info["border_color"]
                        break
                if color_name == OPERATIONS["eraser"]["name"]:
                    text_color = OPERATIONS["eraser"]["text_color"]
                    border_color = OPERATIONS["eraser"]["border_color"]
            else:
                for action, info in OPERATIONS.items():
                    if info["name"] == self.current_text:
                        text_color = info["text_color"]
                        border_color = info["border_color"]
                        break
            self.draw_persian_text(final_frame, self.current_text, (RESOLUTIONS['cam_width'] - 20, 30), text_color, border_color, progress)

        self.current_frame = final_frame
        self.current_artwork = artwork_display

    def draw_persian_text(self, image, text, position, text_color, border_color, anim_progress):
        """Draw Persian text on the image with animation."""
        try:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image, 'RGBA')
            
            if platform.system() == "Windows":
                reshaped_text = arabic_reshaper.reshape(text)
                display_text = get_display(reshaped_text)
            else:
                display_text = text
            
            # Use getbbox instead of getsize for Pillow compatibility
            bbox = self.font.getbbox(display_text)
            text_w = bbox[2] - bbox[0]  # Right - Left
            text_h = bbox[3] - bbox[1]  # Bottom - Top
            text_x = position[0] - text_w
            alpha = int(255 * anim_progress)
            scale = 1.0 + 0.2 * (1.0 - anim_progress)
            bg_alpha = int(128 * anim_progress)
            
            start_border_color = (100, 100, 100)
            animated_border = tuple(
                int(start_border_color[i] + (border_color[i] - start_border_color[i]) * anim_progress)
                for i in range(3)
            ) + (alpha,)
            
            margin = 10
            scaled_w = text_w * scale
            scaled_h = text_h * scale
            offset_x = (scaled_w - text_w) / 2
            offset_y = (scaled_h - text_h) / 2
            
            draw.rounded_rectangle(
                (text_x-margin-offset_x, position[1]-margin-offset_y, text_x+text_w+margin+offset_x, position[1]+text_h+margin+offset_y),
                radius=5, fill=(0, 0, 0, bg_alpha)
            )
            draw.rounded_rectangle(
                (text_x-margin-offset_x, position[1]-margin-offset_y, text_x+text_w+margin+offset_x, position[1]+text_h+margin+offset_y),
                radius=5, outline=animated_border, width=2
            )
            draw.text((text_x, position[1]), display_text, font=self.font, fill=(*text_color, alpha))
            image[:] = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Error rendering Persian text: {e}")

    def refresh_display(self):
        """Refresh the display with the latest frame and artwork."""
        if hasattr(self, 'current_frame') and hasattr(self, 'current_artwork') and self.current_frame is not None and self.current_artwork is not None:
            try:
                frame_resized = cv2.resize(self.current_frame, (RESOLUTIONS['cam_width'], self.current_artwork.shape[0]))
                combined_frame = np.hstack((frame_resized, self.current_artwork))
                combined_frame = cv2.resize(combined_frame, (RESOLUTIONS['final_width'], RESOLUTIONS['final_height']))
                h, w, c = combined_frame.shape
                qimage = QImage(combined_frame.data, w, h, w * c, QImage.Format.Format_RGB888)
                self.display_label.setPixmap(QPixmap.fromImage(qimage))
            except Exception as e:
                print(f"Error in refresh_display: {e}")

    def closeEvent(self, event):
        """Clean up resources on close."""
        self.video_thread.stop()
        hands.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    window = PaintingApp()
    window.show()
    sys.exit(app.exec())