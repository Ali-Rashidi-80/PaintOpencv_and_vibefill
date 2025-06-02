import cv2
import numpy as np
import os
import tkinter as tk
from tkinter import messagebox, filedialog
import HandModule as hm
from PIL import Image, ImageTk

# تنظیمات پیش‌فرض
thickness = 15  # ضخامت پیش‌فرض قلم
colors = {
    "purple": (255, 0, 255),
    "green": (0, 255, 0),
    "red": (0, 0, 255),
    "blue": (255, 0, 0),
    "black": (0, 0, 0),
}
color = colors["blue"]  # رنگ پیش‌فرض

# مسیرهای نسبی برای ذخیره نقاشی‌ها و ابزارها
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # مسیر پایه
SAVE_PATH = os.path.join(BASE_DIR, "drawings")  # مسیر ذخیره نقاشی‌ها
TOOLBAR_PATH = os.path.join(BASE_DIR, "toolbar")  # مسیر ابزارها

# بارگذاری ابزارها
toolbars = os.listdir(TOOLBAR_PATH)  # لیست ابزارها
toolbar = [cv2.imread(os.path.join(TOOLBAR_PATH, tool)) for tool in toolbars if cv2.imread(os.path.join(TOOLBAR_PATH, tool)) is not None]

# اطمینان از بارگذاری صحیح تصاویر ابزار
if len(toolbar) == 0:
    raise ValueError("No toolbar images found or images couldn't be loaded.")

# تخصیص تصاویر ابزار به متغیرها
menu = toolbar[0]  # اطمینان از اینکه تصویر اول به 'menu' اختصاص داده شده است
thicknessup = toolbar[5] if len(toolbar) > 5 else None  # تصویر افزایش ضخامت
thicknessdown = toolbar[4] if len(toolbar) > 4 else None  # تصویر کاهش ضخامت
thick = thicknessup if thicknessup is not None else thicknessdown if thicknessdown is not None else None  # انتخاب ضخامت

# آماده‌سازی ضبط ویدیو
cap = cv2.VideoCapture(0)  # استفاده از دوربین
cap.set(3, 1280)  # تنظیم عرض تصویر
cap.set(4, 720)  # تنظیم ارتفاع تصویر

# تشخیص دست‌ها
detector = hm.Detector(detectionCon=0.7, maxHands=2)  # ایجاد شیء تشخیص دست
blank = np.zeros((720, 1280, 3), np.uint8)  # ایجاد تصویر خالی

# ذخیره نقاشی
def save_drawing(image, save_path, filename):
    if not os.path.exists(save_path):
        os.makedirs(save_path)  # ایجاد دایرکتوری در صورت عدم وجود
    full_path = os.path.join(save_path, filename)  # مسیر کامل فایل
    cv2.imwrite(full_path, image)  # ذخیره تصویر
    print(f"Drawing saved at: {full_path}")  # چاپ مسیر ذخیره

def confirm_save(image):
    root = tk.Tk()
    root.withdraw()  # مخفی کردن پنجره اصلی
    answer = messagebox.askyesno("Save Drawing", "Do you want to save the drawing?")  # سوال برای تایید ذخیره
    if answer:
        filename = filedialog.asksaveasfilename(
            title="Save Drawing As",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if filename:  # اگر نام فایل ارائه شده باشد
            save_drawing(image, os.path.dirname(filename), os.path.basename(filename))  # ذخیره نقاشی

# متغیرهای حلقه اصلی
ready_to_save = False  # آماده برای ذخیره
x0, y0 = 0, 0  # مختصات اولیه
running = False  # متغیر برای کنترل وضعیت برنامه

# تابع برای تغییر وضعیت اجرا
def start_stop_program():
    global running  # استفاده از متغیر جهانی
    running = not running  # تغییر وضعیت
    if not running:  # وقتی که متوقف شده است
        global blank
        blank = np.zeros((720, 1280, 3), np.uint8)  # پاک کردن ناحیه نقاشی
        # بازنشانی منو و ضخامت به حالت اولیه
        global menu, thick
        menu = toolbar[0]  # بازنشانی به تصویر پیش‌فرض ابزار
        thick = thicknessup if thicknessup is not None else thicknessdown if thicknessdown is not None else None
        # پاک کردن نمایش بوم
        canvas_label.config(image="")
        canvas_label.image = None  # پاک کردن تصویر نمایش داده شده در Tkinter

# تابع برای خروج از برنامه
def quit_program():
    # سوال برای تایید خروج
    confirm_quit = messagebox.askyesno("Quit", "Are you sure you want to quit?")
    if confirm_quit:
        root.quit()  # خروج از برنامه

# راه‌اندازی GUI
root = tk.Tk()
root.title("Paint Application")  # عنوان پنجره

# ایجاد بوم برای نمایش تصویر OpenCV
canvas_frame = tk.Frame(root)
canvas_frame.pack(padx=10, pady=10)

canvas_label = tk.Label(canvas_frame)
canvas_label.pack()

# ایجاد یک فریم برای دکمه‌ها
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# ایجاد دکمه شروع/توقف با ظاهر بهبود یافته
start_stop_button = tk.Button(
    button_frame,
    text="Start/Stop",
    command=start_stop_program,
    bg="#4CAF50",  # پس‌زمینه سبز
    fg="white",  # رنگ متن سفید
    font=("Helvetica", 14, "bold"),  # سبک فونت
    relief="flat",  # سبک مسطح برای ظاهر مدرن
    bd=0,  # حذف حاشیه
    highlightbackground="#4CAF50",  # مطابقت با رنگ پس‌زمینه در حالت هایلایت
    activebackground="#45a049",  # سبز تیره‌تر هنگام فشار دادن دکمه
    activeforeground="white",  # رنگ متن هنگام فشار دادن دکمه
    padx=20,  # اضافه کردن فاصله برای عرض
    pady=10,  # اضافه کردن فاصله برای ارتفاع
    cursor="hand2",  # تغییر نشانگر به دست هنگام هاور
)

# افزودن اثر هاور با اتصال به رویدادهای ماوس
def on_enter(e):
    start_stop_button.config(bg="#45a049")  # تغییر رنگ پس‌زمینه

def on_leave(e):
    start_stop_button.config(bg="#4CAF50")  # بازگشت به رنگ اصلی

start_stop_button.bind("<Enter>", on_enter)  # اتصال رویداد ماوس
start_stop_button.bind("<Leave>", on_leave)  # اتصال رویداد ماوس

start_stop_button.pack(side='left', padx=5)  # قرار دادن دکمه در سمت چپ

# ایجاد دکمه خروج
quit_button = tk.Button(
    button_frame,
    text="Quit",
    command=quit_program,
    bg="#f44336",  # پس‌زمینه قرمز
    fg="white",  # رنگ متن سفید
    font=("Helvetica", 14, "bold"),  # سبک فونت
    relief="flat",  # سبک مسطح برای ظاهر مدرن
    bd=0,  # حذف حاشیه
    highlightbackground="#f44336",  # مطابقت با رنگ پس‌زمینه در حالت هایلایت
    activebackground="#d32f2f",  # قرمز تیره‌تر هنگام فشار دادن دکمه
    activeforeground="white",  # رنگ متن هنگام فشار دادن دکمه
    padx=20,  # اضافه کردن فاصله برای عرض
    pady=10,  # اضافه کردن فاصله برای ارتفاع
    cursor="hand2",  # تغییر نشانگر به دست هنگام هاور
)

# افزودن اثر هاور با اتصال به رویدادهای ماوس برای دکمه خروج
def on_enter_quit(e):
    quit_button.config(bg="#d32f2f")  # تغییر رنگ پس‌زمینه

def on_leave_quit(e):
    quit_button.config(bg="#f44336")  # بازگشت به رنگ اصلی

quit_button.bind("<Enter>", on_enter_quit)  # اتصال رویداد ماوس
quit_button.bind("<Leave>", on_leave_quit)  # اتصال رویداد ماوس

quit_button.pack(side='left', padx=5)  # قرار دادن دکمه خروج در سمت چپ

# تابع به‌روزرسانی فریم
def update_frame():
    global running, blank, menu, thick, x0, y0, color, ready_to_save, thickness  # افزودن ضخامت

    if running:
        _, frame = cap.read()  # خواندن فریم از دوربین
        frame = cv2.flip(frame, 1)  # معکوس کردن تصویر
        frame = detector.findHands(frame)  # تشخیص دست‌ها
        landmarklist = detector.Position(frame, draw=False)  # دریافت موقعیت نقاط کلیدی
        fin_pos = []  # لیست وضعیت انگشتان

        # مقداردهی اولیه ضخامت در صورت عدم تنظیم
        if 'thickness' not in globals():
            thickness = 15  # مقدار پیش‌فرض ضخامت

        if len(landmarklist) != 0:  # اگر دست‌ها شناسایی شده باشند
            fin_pos = detector.fing_up()  # وضعیت انگشتان را دریافت کنید
            x1, y1 = landmarklist[8][1], landmarklist[8][2]  # مختصات انگشت اشاره
            x2, y2 = landmarklist[12][1], landmarklist[12][2]  # مختصات انگشت وسط

            # شناسایی ابزار
            if fin_pos[0] and fin_pos[1]:  # حالت انتخاب ابزار
                x0, y0 = 0, 0  # مقداردهی اولیه برای x0 و y0
                if x1 > 1133 and 125 < y1 < 472:  # بررسی ناحیه ابزار
                    if 125 <= y1 < 300:
                        thick = thicknessup  # انتخاب ضخامت بالا
                        thickness = 15
                    elif 300 <= y1 < 472:
                        thick = thicknessdown  # انتخاب ضخامت پایین
                        thickness = 30

                if y1 < 125:  # انتخاب رنگ
                    if 250 < x1 < 450:
                        color = colors["blue"]  # رنگ آبی
                        menu = toolbar[0]
                    elif 550 < x1 < 750:
                        color = colors["purple"]  # رنگ بنفش
                        menu = toolbar[1]
                    elif 800 < x1 < 950:
                        color = colors["green"]  # رنگ سبز
                        menu = toolbar[2]
                    elif 1050 < x1 < 1200:
                        color = colors["black"]  # رنگ سیاه
                        menu = toolbar[3]

                cv2.rectangle(frame, (x1, y1 - 20), (x2, y2 + 20), color, -1)  # رسم مستطیل برای انتخاب رنگ

            # حالت نقاشی
            if fin_pos[0] and not fin_pos[1]:  # اگر فقط انگشت اشاره بالا باشد
                if x0 == 0 and y0 == 0:
                    x0, y0 = x1, y1  # مقداردهی اولیه برای x0 و y0
                if 0 <= x1 < 1280 and 0 <= y1 < 720:  # بررسی محدوده
                    cv2.circle(frame, (x1, y1), 12, color, -1)  # رسم دایره
                    if color == colors["black"]:  # اگر رنگ پاک‌کن باشد
                        cv2.line(frame, (x0, y0), (x1, y1), color, thickness + 25)  # خط پاک‌کن
                        cv2.line(blank, (x0, y0), (x1, y1), color, thickness + 25)  # خط پاک‌کن در تصویر خالی
                    else:
                        cv2.line(frame, (x0, y0), (x1, y1), color, thickness)  # رسم خط
                        cv2.line(blank, (x0, y0), (x1, y1), color, thickness)  # رسم خط در تصویر خالی
                    x0, y0 = x1, y1  # به‌روزرسانی مختصات

            # ذخیره‌سازی
            if all(finger == 1 for finger in fin_pos) and len(fin_pos) == 5:  # اگر همه انگشتان بالا باشند
                if ready_to_save:
                    confirm_save(blank)  # تایید ذخیره
                    blank = np.zeros((720, 1280, 3), np.uint8)  # بازنشانی تصویر خالی بعد از ذخیره
                    ready_to_save = False

        if len(landmarklist) == 0:  # اگر دستی در کادر نیست
            ready_to_save = True  # آماده برای ذخیره

        # نمایش ابزارها و نقاشی
        Gray = cv2.cvtColor(blank, cv2.COLOR_BGR2GRAY)  # تبدیل تصویر خالی به خاکستری
        _, Inv = cv2.threshold(Gray, 0, 255, cv2.THRESH_BINARY_INV)  # معکوس کردن تصویر
        Inv = cv2.cvtColor(Inv, cv2.COLOR_GRAY2BGR)  # تبدیل به رنگی
        frame = cv2.bitwise_and(frame, Inv)  # ترکیب تصویر
        frame = cv2.bitwise_or(frame, blank)  # ترکیب تصویر خالی
        frame[0:125, 0:1280] = menu  # نمایش منو
        frame[125:475, 1130:1280] = thick  # نمایش ضخامت

        # تبدیل فریم به فرمت قابل نمایش در Tkinter
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # تبدیل رنگ BGR به RGB
        image = Image.fromarray(image)  # تبدیل آرایه به تصویر
        image = ImageTk.PhotoImage(image)  # تبدیل تصویر به فرمت قابل نمایش در Tkinter

        # به‌روزرسانی تصویر در لیبل Tkinter
        canvas_label.config(image=image)
        canvas_label.image = image  # ذخیره تصویر برای جلوگیری از جمع‌آوری زباله

    # درخواست به‌روزرسانی فریم
    root.after(10, update_frame)  # به‌روزرسانی هر 10 میلی‌ثانیه

update_frame()  # شروع به‌روزرسانی فریم‌ها
root.mainloop()  # اجرای حلقه اصلی Tkinter