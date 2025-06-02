import sys, os, platform, time, glob, threading, cv2, json
import numpy as np
import mediapipe as mp
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QTabWidget, QGridLayout,
                             QScrollArea, QDialog, QDialogButtonBox, QTextEdit, QFileDialog,
                             QGroupBox, QSpinBox, QMessageBox)
from PyQt6.QtGui import QImage, QPixmap, QColor, QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PIL import Image, ImageDraw, ImageFont
from queue import Queue
import shutil
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
    'canvas_height': 301
}

# Blur settings
DEFAULT_BLUR = True

# Color definitions
COLORS = {
    "red": {"rgb": (0, 0, 255), "name": "قرمز", "text_color": (255, 0, 0), "border_color": (255, 0, 0)},
    "green": {"rgb": (0, 255, 0), "name": "سبز", "text_color": (0, 255, 0), "border_color": (0, 255, 0)},
    "blue": {"rgb": (255, 0, 0), "name": "آبی", "text_color": (0, 0, 255), "border_color": (0, 0, 255)},
    "yellow": {"rgb": (0, 255, 255), "name": "زرد", "text_color": (255, 255, 0), "border_color": (255, 255, 0)},
    "orange": {"rgb": (0, 165, 255), "name": "نارنجی", "text_color": (255, 165, 0), "border_color": (255, 165, 0)},
    "crimson": {"rgb": (0, 0, 128), "name": "زرشکی", "text_color": (128, 0, 0), "border_color": (128, 0, 0)},
    "purple": {"rgb": (128, 0, 128), "name": "بنفش", "text_color": (128, 0, 128), "border_color": (128, 0, 128)},
    "brown": {"rgb": (42, 42, 165), "name": "قهوه‌ای", "text_color": (165, 42, 42), "border_color": (165, 42, 42)},
    "pink": {"rgb": (203, 192, 255), "name": "صورتی", "text_color": (255, 192, 203), "border_color": (255, 192, 203)},
    "cyan": {"rgb": (255, 255, 0), "name": "فیروزه‌ای", "text_color": (0, 255, 255), "border_color": (0, 255, 255)},
    "magenta": {"rgb": (255, 0, 255), "name": "سرخابی", "text_color": (255, 0, 255), "border_color": (255, 0, 255)},
    "white": {"rgb": (255, 255, 255), "name": "سفید", "text_color": (255, 255, 255), "border_color": (255, 255, 255)},
    "gray": {"rgb": (128, 128, 128), "name": "خاکستری", "text_color": (128, 128, 128), "border_color": (128, 128, 128)},
    "light_blue": {"rgb": (255, 191, 0), "name": "آبی روشن", "text_color": (0, 191, 255), "border_color": (0, 191, 255)},
    "dark_blue": {"rgb": (139, 0, 0), "name": "آبی تیره", "text_color": (0, 0, 139), "border_color": (0, 0, 139)},
    "light_green": {"rgb": (144, 238, 144), "name": "سبز روشن", "text_color": (144, 238, 144), "border_color": (144, 238, 144)},
    "dark_green": {"rgb": (0, 100, 0), "name": "سبز تیره", "text_color": (0, 100, 0), "border_color": (0, 100, 0)},
    "olive": {"rgb": (0, 128, 128), "name": "زیتونی", "text_color": (128, 128, 0), "border_color": (128, 128, 0)},
    "teal": {"rgb": (128, 128, 0), "name": "سبزآبی", "text_color": (0, 128, 128), "border_color": (0, 128, 128)},
    "violet": {"rgb": (238, 130, 238), "name": "بنفش روشن", "text_color": (238, 130, 238), "border_color": (238, 130, 238)},
    "gold": {"rgb": (0, 215, 255), "name": "طلایی", "text_color": (255, 215, 0), "border_color": (255, 215, 0)},
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

# Mediapipe setup with improved confidence thresholds
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.6, min_tracking_confidence=0.6)

# Preprocessing function for camera image with adaptive lighting correction
def preprocess_camera_image(image, hardware_backend):
    try:
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge((l, a, b))
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        mean_brightness = np.mean(cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY))
        if mean_brightness < 100:
            enhanced = cv2.convertScaleAbs(enhanced, alpha=1.2, beta=10)
        elif mean_brightness > 180:
            enhanced = cv2.convertScaleAbs(enhanced, alpha=0.8, beta=-10)
        if hardware_backend == "cuda":
            gpu_image = cv2.cuda_GpuMat()
            gpu_image.upload(enhanced)
            denoised = cv2.cuda.bilateralFilter(gpu_image, d=9, sigmaColor=75, sigmaSpace=75)
            enhanced_image = denoised.download()
        elif hardware_backend == "opencl":
            umat_image = cv2.UMat(enhanced)
            denoised = cv2.bilateralFilter(umat_image, d=9, sigmaColor=75, sigmaSpace=75)
            enhanced_image = cv2.UMat.get(denoised)
        else:
            enhanced_image = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)
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
        pixmap = QPixmap(image_path).scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio)
        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)
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
            QLabel { 
                color: #ecf0f1; 
                font-size: 16px; 
                font-family: 'Arial'; 
                text-align: right; 
            }
            QPushButton { 
                background-color: #4e73df; 
                color: white; 
                border-radius: 5px; 
                padding: 8px; 
                font-size: 16px; 
                min-width: 120px;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
                font-family: 'Arial';
            }
            QPushButton:hover { background-color: #1cc88a; box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.4); }
            QComboBox, QSpinBox { 
                background-color: #34495e; 
                color: #ecf0f1; 
                border: 1px solid #4e73df; 
                padding: 5px; 
                font-size: 16px; 
                border-radius: 5px; 
                min-width: 120px;
                box-shadow: 1px 1px 3px rgba(0, 0, 0, 0.2);
                font-family: 'Arial';
                text-align: right;
            }
            QSpinBox { 
                qproperty-alignment: 'AlignCenter'; 
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
                padding: 8px; 
                border-bottom: 1px solid #4e73df;
            }
            QTabWidget::pane { border: 1px solid #4e73df; background-color: #34495e; }
            QTabBar::tab { 
                background: #4e73df; 
                color: white; 
                padding: 8px 18px; 
                font-size: 16px; 
                border-top-left-radius: 8px; 
                border-top-right-radius: 8px; 
                margin-right: 2px;
                font-family: 'Arial';
            }
            QTabBar::tab:selected { 
                background: #1cc88a; 
                font-weight: bold; 
                border-bottom: 3px solid #ffffff; 
            }
            QTabBar::tab:!selected { 
                background: #2c3e50; 
                color: #b0bec5; 
            }
            QTabBar::tab:hover:!selected { 
                background: #546e7a; 
                color: #ffffff; 
            }
            QScrollArea { 
                background-color: #34495e; 
                border: none; 
                border-radius: 8px; 
            }
            QTextEdit { 
                background-color: rgba(52, 73, 94, 0.9); 
                color: #ecf0f1; 
                border: 1px solid #4e73df; 
                border-radius: 8px; 
                padding: 10px; 
                font-size: 16px; 
                font-family: 'Arial';
            }
            QGroupBox { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #34495e, stop:1 #2c3e50); 
                border: 2px solid #4e73df; 
                border-radius: 8px; 
                margin: 15px; 
                font-size: 16px; 
                color: #ecf0f1; 
                font-weight: bold; 
                padding: 15px;
                font-family: 'Arial';
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                subcontrol-position: top center; 
                padding: 0 10px; 
                background-color: #1cc88a; 
                color: white; 
                border-radius: 5px; 
                font-size: 16px; 
                font-family: 'Arial';
            }
            QMessageBox { 
                background-color: #34495e; 
                color: #ecf0f1; 
                font-size: 16px; 
                font-family: 'Arial'; 
            }
            QMessageBox QLabel { 
                color: #ecf0f1; 
                font-size: 16px; 
                font-family: 'Arial'; 
                text-align: right; 
            }
            QMessageBox QPushButton { 
                background-color: #4e73df; 
                color: white; 
                border-radius: 5px; 
                padding: 8px; 
                font-size: 16px; 
                min-width: 80px; 
                font-family: 'Arial'; 
            }
            QMessageBox QPushButton:hover { 
                background-color: #1cc88a; 
            }
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
        self.left_hand_frame_counter = 0
        self.right_hand_frame_counter = 0
        self.min_frames_for_unblur = 15
        self.min_frames_for_right_hand = 5
        self.last_pinch_time = 0  # Track the last time a pinch action occurred
        self.pinch_cooldown = 0.2  # Cooldown period in seconds to prevent rapid repeated coloring
        # Initialize settings
        self.load_settings()

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
        self.timer.start(33)

        self.showMaximized()

    def load_settings(self):
        """Load settings from hidden JSON file or set defaults."""
        self.blur_amount = 81
        self.padding = 130
        self.max_image_size = (2000, 2000)
        self.gallery_columns = 4
        settings_file = ".paint_settings.json"
        try:
            with open(settings_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.blur_amount = settings.get("blur_amount", 81)
                if self.blur_amount % 2 == 0:
                    self.blur_amount += 1
                self.padding = settings.get("padding", 130)
                self.max_image_size = (
                    settings.get("max_image_width", 2000),
                    settings.get("max_image_height", 2000)
                )
                self.gallery_columns = settings.get("gallery_columns", 4)
                # Validate loaded values
                self.blur_amount = max(1, min(201, self.blur_amount))
                self.padding = max(50, min(300, self.padding))
                self.max_image_size = (
                    max(500, min(5000, self.max_image_size[0])),
                    max(500, min(5000, self.max_image_size[1]))
                )
                self.gallery_columns = max(2, min(6, self.gallery_columns))
                print(f"Loaded settings from {settings_file}")
        except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
            print(f"Error loading settings from {settings_file}: {e}, using defaults")
            self.save_settings()  # Create default settings file

    def save_settings(self):
        """Save settings to hidden JSON file."""
        settings_file = ".paint_settings.json"
        settings = {
            "blur_amount": self.blur_amount,
            "padding": self.padding,
            "max_image_width": self.max_image_size[0],
            "max_image_height": self.max_image_size[1],
            "gallery_columns": self.gallery_columns
        }
        try:
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
            # Make file hidden
            if platform.system() == "Windows":
                os.system(f'attrib +h "{settings_file}"')
            print(f"Saved settings to {settings_file}")
        except Exception as e:
            print(f"Error saving settings to {settings_file}: {e}")

    def setup_ui(self):
        main_widget = QWidget()
        main_widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        tabs = QTabWidget()
        tabs.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        main_layout.addWidget(tabs)
        main_layout.setStretchFactor(tabs, 1)

        # Painting tab
        painting_tab = QWidget()
        painting_layout = QVBoxLayout(painting_tab)
        painting_layout.setContentsMargins(0, 0, 0, 0)
        painting_layout.setSpacing(10)
        tabs.addTab(painting_tab, "نقاشی")

        display_widget = QWidget()
        display_layout = QHBoxLayout(display_widget)
        display_layout.setContentsMargins(0, 0, 0, 0)
        display_layout.setSpacing(0)
        self.display_label = QLabel()
        self.display_label.setFixedSize(RESOLUTIONS['final_width'], RESOLUTIONS['final_height'])
        self.display_label.setStyleSheet("border: 1px solid #4e73df; border-radius: 8px;")
        display_layout.addWidget(self.display_label)
        display_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        painting_layout.addWidget(display_widget)

        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(20)
        controls_layout.addStretch(1)

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

        design_layout = QVBoxLayout()
        design_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        design_layout.setSpacing(5)
        add_design_button = QPushButton("افزودن طرح جدید")
        add_design_button.clicked.connect(self.add_new_design)
        design_layout.addWidget(QLabel("طرح جدید:"))
        design_layout.addWidget(add_design_button)
        design_layout.addStretch(1)
        controls_layout.addLayout(design_layout)

        controls_layout.addStretch(1)
        painting_layout.addWidget(controls_widget)

        # Initialize backend_label as an instance attribute
        self.backend_label = QLabel(f"شتاب‌دهنده: {self.video_thread.hardware_backend}")
        self.backend_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.backend_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #ecf0f1; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4e73df, stop:1 #1cc88a); 
            padding: 8px; 
            border-radius: 5px; 
            border: 1px solid #ffffff; 
            font-family: 'Arial';
        """)
        painting_layout.addWidget(self.backend_label)

        painting_layout.addStretch(1)

        # Gallery tab
        gallery_tab = QWidget()
        gallery_layout = QVBoxLayout(gallery_tab)
        gallery_layout.setContentsMargins(10, 10, 10, 10)
        gallery_layout.setSpacing(10)
        tabs.addTab(gallery_tab, "گالری")

        gallery_header = QLabel("✨ گالری آثار شما ✨")
        gallery_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gallery_header.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: #ffffff; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4e73df, stop:1 #1cc88a); 
            padding: 10px; 
            border-radius: 8px; 
            margin-bottom: 10px; 
            font-family: 'Arial';
        """)
        gallery_layout.addWidget(gallery_header)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { 
                background-color: #34495e; 
                border: none; 
                border-radius: 8px; 
            }
            QScrollBar:vertical { 
                border: none; 
                background: #2c3e50; 
                width: 10px; 
                margin: 0px 0px 0px 0px; 
                border-radius: 5px; 
            }
            QScrollBar::handle:vertical { 
                background: #4e73df; 
                min-height: 20px; 
                border-radius: 5px; 
            }
            QScrollBar::handle:vertical:hover { 
                background: #1cc88a; 
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { 
                height: 0px; 
            }
        """)
        gallery_widget = QWidget()
        self.gallery_grid = QGridLayout(gallery_widget)
        self.gallery_grid.setContentsMargins(0, 0, 0, 0)
        self.gallery_grid.setSpacing(10)
        scroll_area.setWidget(gallery_widget)
        gallery_layout.addWidget(scroll_area)

        self.load_gallery()

        # Settings tab
        settings_tab = QWidget()
        settings_tab.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        settings_layout = QVBoxLayout(settings_tab)
        settings_layout.setContentsMargins(500, 40, 500, 15)
        settings_layout.setSpacing(15)
        tabs.addTab(settings_tab, "تنظیمات")

        settings_header = QLabel("⚙️ تنظیمات برنامه ⚙️")
        settings_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        settings_header.setStyleSheet("""
            font-size: 22px; 
            font-weight: bold; 
            color: #ffffff; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4e73df, stop:1 #1cc88a); 
            padding: 10px; 
            border-radius: 8px; 
            margin-bottom: 15px; 
            font-family: 'Arial';
        """)
        settings_layout.addWidget(settings_header)

        # Image Processing Settings
        image_settings_group = QGroupBox("📷 تنظیمات پردازش تصویر")
        image_settings_group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        image_settings_layout = QGridLayout(image_settings_group)
        image_settings_layout.setContentsMargins(15, 15, 15, 15)
        image_settings_layout.setHorizontalSpacing(10)
        image_settings_layout.setVerticalSpacing(15)

        self.blur_spinbox = QSpinBox()
        self.blur_spinbox.setRange(1, 201)
        self.blur_spinbox.setSingleStep(2)
        self.blur_spinbox.setValue(self.blur_amount)
        self.blur_spinbox.setToolTip("میزان بلور تصویر وب‌کم را تنظیم کنید")
        image_settings_layout.addWidget(QLabel("میزان بلور (پیکسل):"), 0, 0, Qt.AlignmentFlag.AlignRight)
        image_settings_layout.addWidget(self.blur_spinbox, 0, 1, Qt.AlignmentFlag.AlignLeft)

        self.padding_spinbox = QSpinBox()
        self.padding_spinbox.setRange(50, 300)
        self.padding_spinbox.setSingleStep(10)
        self.padding_spinbox.setValue(self.padding)
        self.padding_spinbox.setToolTip("فاصله حاشیه اطراف بوم نقاشی را تنظیم کنید")
        image_settings_layout.addWidget(QLabel("فاصله حاشیه (پیکسل):"), 1, 0, Qt.AlignmentFlag.AlignRight)
        image_settings_layout.addWidget(self.padding_spinbox, 1, 1, Qt.AlignmentFlag.AlignLeft)

        self.max_width_spinbox = QSpinBox()
        self.max_width_spinbox.setRange(500, 5000)
        self.max_width_spinbox.setSingleStep(100)
        self.max_width_spinbox.setValue(self.max_image_size[0])
        self.max_width_spinbox.setToolTip("حداکثر عرض تصویر ورودی را تنظیم کنید")
        image_settings_layout.addWidget(QLabel("حداکثر عرض تصویر (پیکسل):"), 2, 0, Qt.AlignmentFlag.AlignRight)
        image_settings_layout.addWidget(self.max_width_spinbox, 2, 1, Qt.AlignmentFlag.AlignLeft)

        self.max_height_spinbox = QSpinBox()
        self.max_height_spinbox.setRange(500, 5000)
        self.max_height_spinbox.setSingleStep(100)
        self.max_height_spinbox.setValue(self.max_image_size[1])
        self.max_height_spinbox.setToolTip("حداکثر ارتفاع تصویر ورودی را تنظیم کنید")
        image_settings_layout.addWidget(QLabel("حداکثر ارتفاع تصویر (پیکسل):"), 3, 0, Qt.AlignmentFlag.AlignRight)
        image_settings_layout.addWidget(self.max_height_spinbox, 3, 1, Qt.AlignmentFlag.AlignLeft)

        settings_layout.addWidget(image_settings_group)

        # Gallery Settings
        gallery_settings_group = QGroupBox("🖼️ تنظیمات گالری")
        gallery_settings_group.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        gallery_settings_layout = QGridLayout(gallery_settings_group)
        gallery_settings_layout.setContentsMargins(15, 15, 15, 15)
        gallery_settings_layout.setHorizontalSpacing(10)
        gallery_settings_layout.setVerticalSpacing(15)

        self.columns_spinbox = QSpinBox()
        self.columns_spinbox.setRange(2, 6)
        self.columns_spinbox.setSingleStep(1)
        self.columns_spinbox.setValue(self.gallery_columns)
        self.columns_spinbox.setToolTip("تعداد ستون‌های گالری را تنظیم کنید")
        gallery_settings_layout.addWidget(QLabel("تعداد ستون‌های گالری:"), 0, 0, Qt.AlignmentFlag.AlignRight)
        gallery_settings_layout.addWidget(self.columns_spinbox, 0, 1, Qt.AlignmentFlag.AlignLeft)

        settings_layout.addWidget(gallery_settings_group)

        # Apply Button
        apply_button = QPushButton("اعمال تنظیمات")
        apply_button.setStyleSheet("""
            QPushButton { 
                background-color: #4e73df; 
                color: white; 
                border-radius: 5px; 
                padding: 8px; 
                font-size: 16px; 
                min-width: 150px; 
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.3);
                font-family: 'Arial';
            }
            QPushButton:hover { 
                background-color: #1cc88a; 
                box-shadow: 3px 3px 8px rgba(0, 0, 0, 0.4); 
            }
        """)
        apply_button.clicked.connect(self.apply_settings)
        settings_layout.addWidget(apply_button, alignment=Qt.AlignmentFlag.AlignCenter)

        settings_layout.addStretch(1)

# About tab
        about_tab = QWidget()
        about_layout = QVBoxLayout(about_tab)
        about_layout.setContentsMargins(8, 8, 8, 8)
        about_layout.setSpacing(6)
        tabs.addTab(about_tab, "درباره")

        about_header = QLabel("🎨 با نقاشی دیجیتال آفلاین آشنا شو! 🎨")
        about_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_header.setStyleSheet("""
            font-size: 28px; 
            font-weight: bold; 
            color: #ffffff; 
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3a5ba0, stop:0.5 #00c851, stop:1 #ff4444); 
            padding: 15px; 
            border-radius: 12px; 
            margin-bottom: 12px; 
            text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.6); 
            font-family: 'Arial';
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        """)
        about_layout.addWidget(about_header)

        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        about_text.setStyleSheet("""
            background-color: rgba(44, 62, 80, 0.95); 
            color: #e0f7fa; 
            border: 2px solid #3a5ba0; 
            border-radius: 12px; 
            padding: 18px; 
            font-size: 18px; 
            line-height: 2.0; 
            font-family: 'Arial'; 
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
        """)
        about_text.setHtml("""
            <h2 style='color: #00c851; text-align: center; text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.4);'>✨ سلام به دنیای رنگ‌ها و خلاقیت! ✨</h2>
            <p style='color: #e0f7fa; font-size: 18px; line-height: 2.0; text-align: justify;'>
                نقاشی دیجیتال آفلاین یه برنامه خیلی ساده و باحاله که بهت اجازه می‌ده با دستات و وب‌کم، نقاشی‌های قشنگ بکشی! نیازی به اینترنت نداری و می‌تونی هر وقت که دلت خواست، یه اثر هنری خلق کنی. فرقی نمی‌کنه حرفه‌ای باشی یا فقط بخوای یه سرگرمی جذاب داشته باشی، این برنامه برای همه‌ست!
            </p>
            <h3 style='color: #3a5ba0; text-align: center; margin-top: 18px;'>چیزای باحالی که می‌تونی باهاش انجام بدی:</h3>
            <ul style='color: #e0f7fa; font-size: 18px; line-height: 2.2;'>
                <li>🖐️ <b>نقاشی با دستات:</b> دست راستت می‌شه قلم‌مو، دست چپت هم می‌تونه تصویر دوربین رو واضح‌تر کنه.</li>
                <li>🎨 <b>رنگ‌آمیزی و پاک کردن:</b> با یه روش ساده می‌تونی قسمت‌های مختلف رو رنگ کنی یا اگه اشتباه کردی، پاکش کنی.</li>
                <li>⚡ <b>سریع و روان:</b> اگه سیستمت قوی باشه، برنامه از قدرت کارت گرافیک استفاده می‌کنه تا همه‌چیز سریع‌تر بشه.</li>
                <li>🌟 <b>تصویر بهتر:</b> تصویر وب‌کم رو واضح‌تر می‌کنه تا بهتر بتونی نقاشی بکشی.</li>
                <li>🖼️ <b>گالری قشنگ:</b> نقاشی‌هات رو با تاریخ شمسی ذخیره می‌کنه و می‌تونی هر وقت بخوای ببینیشون.</li>
                <li>📱 <b>کار کردن باهاش راحته:</b> همه‌چیز طوری طراحی شده که به‌راحتی بتونی ازش استفاده کنی، با نوشته‌های فارسی و قشنگ.</li>
                <li>🔄 <b>امکانات جورواجور:</b> می‌تونی نقاشی رو برگردونی به قبل، کامل پاکش کنی، بین طرح‌ها جابه‌جا شی یا ذخیره‌شون کنی.</li>
                <li>🖥️ <b>هر عکسی می‌تونی بذاری:</b> عکس‌های PNG، JPG یا حتی WebP رو می‌تونی بیاری و روشون نقاشی کنی.</li>
                <li>🚫 <b>اگه مشکلی پیش بیاد:</b> اگه یه وقت خطایی بشه، برنامه بهت می‌گه چی شده و چطور می‌تونی درستش کنی.</li>
                <li>⚙️ <b>تنظیمات دلخواه:</b> می‌تونی خودت تنظیم کنی که تصویر چقدر تار یا واضح باشه، یا گالری‌ت چندتا ستون داشته باشه.</li>
            </ul>
            <p style='color: #e0f7fa; font-size: 18px; line-height: 2.0; text-align: justify; margin-top: 18px;'>
                این برنامه بهت این امکان رو می‌ده که هر چی تو ذهنت داری رو روی صفحه بیاری! فقط کافیه عکسات رو توی پوشه <b>draw</b> بذاری، بعدش رنگ‌آمیزی کنی و توی گالری ذخیره‌شون کنی. آماده‌ای که یه نقاشی قشنگ بکشی؟ بیا شروع کنیم!
            </p>
            <p style='color: #00c851; font-size: 18px; text-align: center; font-weight: bold; margin-top: 18px; text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);'>
                🌟 نقاشی‌هات دنیا رو قشنگ‌تر می‌کنن! 🌟
            </p>
            <p style='color: #00c851; font-size: 18px; text-align: center; font-weight: bold; margin-top: 18px; text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);'>
                ساخته شده توسط: Ali Rashidi (@a_ra_80)
            </p>
            <p style='color: #00c851; font-size: 18px; text-align: center; font-weight: bold; margin-top: 18px; text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.3);'>
                اگه سؤالی داری یا پیشنهادی به ذهنت رسید: t.me/WriteYourWay
            </p>
        """)
        about_layout.addWidget(about_text)

    def apply_settings(self):
        """Apply settings from the settings tab, save to JSON, and reload if necessary."""
        new_blur = self.blur_spinbox.value()
        new_padding = self.padding_spinbox.value()
        new_max_width = self.max_width_spinbox.value()
        new_max_height = self.max_height_spinbox.value()
        new_columns = self.columns_spinbox.value()

        if new_blur % 2 == 0:
            new_blur += 1
            self.blur_spinbox.setValue(new_blur)

        reload_image_required = new_padding != self.padding
        reload_gallery_required = new_columns != self.gallery_columns

        self.blur_amount = new_blur
        self.padding = new_padding
        self.max_image_size = (new_max_width, new_max_height)
        self.gallery_columns = new_columns

        self.save_settings()

        if reload_image_required:
            self.load_image(self.current_image_index)
        if reload_gallery_required:
            self.load_gallery()

        # Show success popup
        msg = QMessageBox(self)
        msg.setWindowTitle("موفقیت")
        msg.setText("تنظیمات با موفقیت اعمال شد")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        msg.exec()

        print(f"Settings applied: blur_amount={self.blur_amount}, padding={self.padding}, max_image_size={self.max_image_size}, gallery_columns={self.gallery_columns}")

    def add_new_design(self):
        """Open a file dialog to select a new design, validate, convert to PNG, and load it."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Images (*.png *.jpg *.jpeg *.webp *.bmp)")
        if file_dialog.exec():
            selected_file = file_dialog.selectedFiles()[0]
            draw_folder = "draw"
            os.makedirs(draw_folder, exist_ok=True)
            file_name = os.path.basename(selected_file)
            base_name = os.path.splitext(file_name)[0]
            destination_path = os.path.join(draw_folder, f"{base_name}.png")

            try:
                with Image.open(selected_file) as img:
                    width, height = img.size
                    if width > self.max_image_size[0] or height > self.max_image_size[1]:
                        self.current_text = f"خطا: تصویر بزرگ‌تر از حد مجاز ({self.max_image_size[0]}x{self.max_image_size[1]} پیکسل) است"
                        self.text_start_time = time.time()
                        print(f"Error: Image dimensions {width}x{height} exceed maximum {self.max_image_size}")
                        return

                if os.path.exists(destination_path):
                    self.current_text = "خطا: فایل قبلاً در پوشه طرح وجود دارد"
                    self.text_start_time = time.time()
                    print(f"Error: File {destination_path} already exists")
                    return

                try:
                    with Image.open(selected_file) as img:
                        img = img.convert("RGB")
                        img.save(destination_path, "PNG", quality=95)
                    print(f"Converted image to PNG: {destination_path}")

                    self.image_files = glob.glob("draw/*.png")
                    self.current_image_index = self.image_files.index(destination_path)
                    if self.load_image(self.current_image_index):
                        self.current_text = "طرح جدید با موفقیت اضافه شد"
                        self.text_start_time = time.time()
                    else:
                        self.current_text = "خطا: بارگذاری تصویر ناموفق بود"
                        self.text_start_time = time.time()
                        print(f"Error: Failed to load image {destination_path}")
                except Exception as e:
                    self.current_text = f"خطا: {str(e)}"
                    self.text_start_time = time.time()
                    print(f"Error during file conversion: {e}")
                    return
            except Exception as e:
                self.current_text = f"خطا: {str(e)}"
                self.text_start_time = time.time()
                print(f"Error validating image: {e}")
                return

    def load_gallery(self):
        """Load images into the gallery with dynamic column count."""
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
            image_label.setStyleSheet("""
                border: 1px solid #4e73df; 
                padding: 5px; 
                border-radius: 8px; 
                background-color: #2c3e50; 
            """)
            image_label.mousePressEvent = lambda event, path=img_path: self.show_image_modal(path)
            ctime = os.path.getctime(img_path)
            if PERSIANTOOLS_AVAILABLE:
                jalali_dt = JalaliDateTime.fromtimestamp(ctime)
                date_str = jalali_dt.strftime("%Y/%m/%d %H:%M")
                weekday = jalali_dt.weekday()
                persian_weekdays = {
                    0: "شنبه", 1: "یک‌شنبه", 2: "دوشنبه", 3: "سه‌شنبه",
                    4: "چهارشنبه", 5: "پنج‌شنبه", 6: "جمعه"
                }
                weekday_str = persian_weekdays[weekday]
                date_label_text = f"{weekday_str} | {date_str}"
            else:
                date_str = time.strftime("%Y-%m-d %H:%M", time.localtime(ctime))
                date_label_text = f"Unknown Day | {date_str}"
            date_label = QLabel(date_label_text)
            date_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            date_label.setStyleSheet("""
                background-color: #34495e; 
                color: #ecf0f1; 
                border: 1px solid #4e73df; 
                border-radius: 5px; 
                padding: 5px; 
                font-size: 12px; 
                font-weight: bold; 
                text-align: center; 
                font-family: 'Arial';
            """)
            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(5)
            container_layout.addWidget(image_label)
            container_layout.addWidget(date_label)
            container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.gallery_grid.addWidget(container, i // self.gallery_columns, i % self.gallery_columns)

    def show_image_modal(self, image_path):
        modal = ImageModal(image_path, self)
        modal.exec()
        self.load_gallery()

    def load_image(self, index):
        if 0 <= index < len(self.image_files):
            image_path = self.image_files[index]
            self.canvas = cv2.imread(image_path)
            if self.canvas is None:
                print(f"Error: Could not load image {image_path}")
                return False
            self.canvas = preprocess_image(self.canvas)
            self.canvas = cv2.resize(self.canvas, (RESOLUTIONS['canvas_width'], RESOLUTIONS['canvas_height']))
            self.artwork_padded = cv2.copyMakeBorder(
                self.canvas, self.padding, self.padding, self.padding, self.padding,
                cv2.BORDER_CONSTANT, value=(255, 255, 255)
            )
            self.initial_canvas = self.artwork_padded.copy()
            self.canvas = self.artwork_padded.copy()
            gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
            _, self.black_mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY_INV)
            self.black_mask = (self.black_mask == 255).astype(np.uint8) * 255
            self.undo_stack.clear()
            print(f"Loaded image: {image_path}")
            return True
        return False

    def change_color(self):
        color_name = self.color_combo.currentData()
        if color_name:
            self.selected_color = "eraser" if color_name == "eraser" else COLORS[color_name]["rgb"]
            self.coloring_enabled = True
            info = OPERATIONS["eraser"] if color_name == "eraser" else COLORS[color_name]
            self.current_text = f"رنگ: {info['name']}"
            self.text_start_time = time.time()
            print(f"Selected color: {info['name']}, coloring_enabled: {self.coloring_enabled}")

    def perform_action(self, action):
        if not action:
            return
        current_time = time.time()
        if current_time - self.last_action_time[action] > 0.5:
            self.last_action_time[action] = current_time
            self.current_text = OPERATIONS[action]["name"]
            self.text_start_time = current_time
            print(f"Performing action: {action}")
            if action == "eraser":
                self.selected_color = "eraser"
                self.coloring_enabled = True
                print(f"Eraser activated, coloring_enabled: {self.coloring_enabled}")
            elif action == "undo" and self.undo_stack:
                self.canvas = self.undo_stack.pop()
                self.artwork_padded = self.canvas.copy()
                print("Undo performed")
                black_regions = self.black_mask > 0
                self.canvas[black_regions] = self.initial_canvas[black_regions]
                self.artwork_padded[black_regions] = self.initial_canvas[black_regions]
                print("Black lines restored after undo")
            elif action == "reset":
                self.canvas = self.initial_canvas.copy()
                self.artwork_padded = self.canvas.copy()
                self.undo_stack.clear()
                print("Canvas reset")
            elif action == "next" and self.current_image_index < len(self.image_files) - 1:
                self.current_image_index += 1
                self.load_image(self.current_image_index)
                print(f"Next image loaded: {self.current_image_index}")
            elif action == "prev" and self.current_image_index > 0:
                self.current_image_index -= 1
                self.load_image(self.current_image_index)
                print(f"Previous image loaded: {self.current_image_index}")
            elif action == "save":
                gallery_folder = os.path.join("static", "gallery")
                os.makedirs(gallery_folder, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                file_name = f"saved_{timestamp}.png"
                file_path = os.path.join(gallery_folder, file_name)
                cv2.imwrite(file_path, self.artwork_padded)
                print(f"Image saved to {file_path}")
                self.load_gallery()

    def draw_persian_text(self, image, text, position, text_color, border_color, anim_progress):
        try:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            draw = ImageDraw.Draw(pil_image, 'RGBA')
            if platform.system() == "Windows":
                reshaped_text = arabic_reshaper.reshape(text)
                display_text = get_display(reshaped_text)
            else:
                display_text = text
            bbox = self.font.getbbox(display_text)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
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

    def update_frame(self, data):
        frame, hands_results = data
        current_time = time.time()
        x_avg, y_avg = None, None
        pinch_active = False
        is_left_hand_detected_temp = False
        is_right_hand_detected_temp = False
        is_right_hand_confident = False

        landmark_frame = np.zeros_like(frame)
        if hands_results.multi_hand_landmarks and hands_results.multi_handedness:
            for hand_landmarks, handedness in zip(hands_results.multi_hand_landmarks, hands_results.multi_handedness):
                hand_label = handedness.classification[0].label
                confidence = handedness.classification[0].score
                if hand_label == "Left" and confidence > 0.7:
                    is_left_hand_detected_temp = True
                if hand_label == "Right" and confidence > 0.7:
                    is_right_hand_detected_temp = True
                    is_right_hand_confident = True
                    mp_drawing.draw_landmarks(landmark_frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                    index_finger_tip = hand_landmarks.landmark[8]
                    thumb_tip = hand_landmarks.landmark[4]
                    h, w = frame.shape[:2]
                    x_index, y_index = int(index_finger_tip.x * w), int(index_finger_tip.y * h)
                    x_thumb, y_thumb = int(thumb_tip.x * w), int(thumb_tip.y * h)
                    pinch_distance = np.sqrt((x_index - x_thumb) ** 2 + (y_index - y_thumb) ** 2) / w
                    pinch_active = pinch_distance < 0.045
                    # Optimize finger position smoothing for faster response
                    self.finger_positions.append((x_index, y_index))
                    if len(self.finger_positions) > 10:  # Reduced window size for faster response
                        self.finger_positions.pop(0)
                    x_mean = np.mean([pos[0] for pos in self.finger_positions])
                    y_mean = np.mean([pos[1] for pos in self.finger_positions])
                    # Adjusted EMA for quicker reaction
                    self.ema_x = 0.6 * x_mean + (1 - 0.6) * (self.ema_x or x_mean)
                    self.ema_y = 0.6 * y_mean + (1 - 0.6) * (self.ema_y or y_mean)
                    x_avg, y_avg = int(self.ema_x), int(self.ema_y)

        if is_left_hand_detected_temp:
            self.left_hand_frame_counter += 1
        else:
            self.left_hand_frame_counter = max(0, self.left_hand_frame_counter - 1)
        if is_right_hand_detected_temp:
            self.right_hand_frame_counter += 1
        else:
            self.right_hand_frame_counter = max(0, self.right_hand_frame_counter - 1)
        is_left_hand_detected = self.left_hand_frame_counter >= self.min_frames_for_unblur
        is_right_hand_stable = self.right_hand_frame_counter >= self.min_frames_for_right_hand

        final_frame = cv2.GaussianBlur(frame, (self.blur_amount, self.blur_amount), 0) if DEFAULT_BLUR and not is_left_hand_detected else frame.copy()
        mask = landmark_frame > 0
        final_frame[mask] = landmark_frame[mask]

        artwork_display = self.artwork_padded.copy() if self.artwork_padded is not None else np.zeros((RESOLUTIONS['canvas_height'] + 2 * self.padding, RESOLUTIONS['canvas_width'] + 2 * self.padding, 3), dtype=np.uint8)
        
        if x_avg is not None and not is_left_hand_detected and self.canvas is not None and is_right_hand_confident and is_right_hand_stable:
            cam_w, cam_h = RESOLUTIONS['cam_width'], RESOLUTIONS['cam_height']
            art_w, art_h = RESOLUTIONS['canvas_width'] + 2 * self.padding, RESOLUTIONS['canvas_height'] + 2 * self.padding
            x_art = int(x_avg * (art_w / cam_w))
            y_art = int(y_avg * (art_h / cam_h))
            cv2.circle(artwork_display, (x_art, y_art), 5, (0, 0, 255), -1)
            # Check if enough time has passed since the last pinch to allow a new coloring action
            time_since_last_pinch = current_time - self.last_pinch_time
            if pinch_active and not self.pinch_triggered and self.coloring_enabled and time_since_last_pinch > self.pinch_cooldown:
                self.pinch_triggered = True
                self.last_pinch_time = current_time
                if 0 <= x_art < self.canvas.shape[1] and 0 <= y_art < self.canvas.shape[0]:
                    if self.black_mask[y_art, x_art] == 255:
                        print(f"Operation skipped: Point ({x_art}, {y_art}) is on a black line")
                    else:
                        print(f"Pinch at ({x_art}, {y_art}), Canvas shape: {self.canvas.shape}")
                        if len(self.undo_stack) > 100:
                            self.undo_stack = self.undo_stack[-10:]
                        self.undo_stack.append(self.canvas.copy())
                        mask = np.zeros((self.canvas.shape[0] + 2, self.canvas.shape[1] + 2), dtype=np.uint8)
                        if self.selected_color == "eraser":
                            print(f"Erasing at ({x_art}, {y_art})")
                            _, temp_canvas, mask, _ = cv2.floodFill(
                                self.canvas.copy(),
                                mask,
                                (x_art, y_art),
                                (255, 255, 255),
                                loDiff=(30, 30, 30),  # Reduced loDiff/upDiff for faster flood fill
                                upDiff=(30, 30, 30),
                                flags=cv2.FLOODFILL_FIXED_RANGE
                            )
                            region = (mask[1:-1, 1:-1] > 0)
                            print(f"Eraser region shape: {region.shape}, Non-zero pixels: {region.sum()}")
                            if region.sum() > 0:
                                self.canvas[region] = self.initial_canvas[region]
                                black_regions = self.black_mask > 0
                                self.canvas[black_regions] = self.initial_canvas[black_regions]
                                self.artwork_padded = self.canvas.copy()
                                print("Eraser applied successfully, black lines restored")
                            else:
                                print("Warning: No region erased (empty mask)")
                        elif self.selected_color is not None:
                            print(f"Painting at ({x_art}, {y_art}) with color {self.selected_color}")
                            cv2.floodFill(
                                self.canvas,
                                mask,
                                (x_art, y_art),
                                self.selected_color,
                                loDiff=(30, 30, 30),  # Reduced loDiff/upDiff for faster flood fill
                                upDiff=(30, 30, 30),
                                flags=cv2.FLOODFILL_FIXED_RANGE
                            )
                            black_regions = self.black_mask > 0
                            self.canvas[black_regions] = self.initial_canvas[black_regions]
                            self.artwork_padded = self.canvas.copy()
                            print("Painting applied successfully, black lines restored")
            elif not pinch_active:
                self.pinch_triggered = False

        if self.current_text:
            fade_out = True
            if self.current_text.startswith("رنگ:") or self.current_text == OPERATIONS["eraser"]["name"]:
                fade_out = False
            if fade_out and current_time - self.text_start_time > 3.0:
                self.current_text = None
                return
            progress = min((current_time - self.text_start_time) / 0.5, 1.0) if not fade_out else min((current_time - self.text_start_time) / 0.5, 1.0)
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
            elif self.current_text.startswith("طرح جدید با موفقیت اضافه شد"):
                text_color = (255, 255, 255)
                border_color = (0, 200, 200)
            elif self.current_text.startswith("خطا:"):
                text_color = (255, 255, 255)
                border_color = (255, 0, 0)
            else:
                for action, info in OPERATIONS.items():
                    if info["name"] == self.current_text:
                        text_color = info["text_color"]
                        border_color = info["border_color"]
                        break
            self.draw_persian_text(final_frame, self.current_text, (RESOLUTIONS['cam_width'] - 20, 30), text_color, border_color, progress)

        self.current_frame = final_frame
        self.current_artwork = artwork_display

    def refresh_display(self):
        if hasattr(self, 'current_frame') and hasattr(self, 'current_artwork') and self.current_frame is not None and self.current_artwork is not None:
            try:
                frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)
                artwork_rgb = cv2.cvtColor(self.current_artwork, cv2.COLOR_BGR2RGB)
                frame_resized = cv2.resize(frame_rgb, (RESOLUTIONS['cam_width'], artwork_rgb.shape[0]))
                combined_frame = np.hstack((frame_resized, artwork_rgb))
                combined_frame = cv2.resize(combined_frame, (RESOLUTIONS['final_width'], RESOLUTIONS['final_height']))
                h, w, c = combined_frame.shape
                qimage = QImage(combined_frame.data, w, h, w * c, QImage.Format.Format_RGB888)
                self.display_label.setPixmap(QPixmap.fromImage(qimage))
            except Exception as e:
                print(f"Error in refresh_display: {e}")

    def closeEvent(self, event):
        self.video_thread.stop()
        hands.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    window = PaintingApp()
    window.show()
    sys.exit(app.exec())