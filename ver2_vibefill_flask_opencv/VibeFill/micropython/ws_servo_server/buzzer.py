import machine, utime, math

# تنظیم پین بوزر (مثلاً GP15) و راه‌اندازی PWM
buzzer_pin = machine.Pin(12, machine.Pin.OUT)
pwm = machine.PWM(buzzer_pin)

def play_tone(freq, duration):
    """اجرای یک تون ساده با فرکانس و مدت زمان مشخص"""
    pwm.freq(freq)
    pwm.duty_u16(35000)  # افزایش میزان duty cycle برای صدای بلندتر
    utime.sleep_ms(duration)
    pwm.duty_u16(0)
    utime.sleep_ms(10)

def vibrato_tone(base_freq, duration, vibrato_depth=50, vibrato_speed=20):
    """
    اجرای تون با افکت ویبراتو (تکان خوردن فرکانس)
    base_freq: فرکانس پایه (هرتز)
    duration: مدت زمان اجرا به میلی‌ثانیه
    vibrato_depth: دامنه تغییر فرکانس (هرتز)
    vibrato_speed: سرعت ویبراتو (تعداد نوسان در ثانیه)
    """
    update_interval = 5  # زمان به‌روزرسانی هر 5 میلی‌ثانیه
    steps = duration // update_interval
    for i in range(steps):
        current_time = i * update_interval  # زمان جاری به میلی‌ثانیه
        # محاسبه تغییر فرکانس با استفاده از تابع سینوس
        modulation = vibrato_depth * math.sin(2 * math.pi * vibrato_speed * (current_time / 1000))
        current_freq = int(base_freq + modulation)
        pwm.freq(current_freq)
        pwm.duty_u16(35000)
        utime.sleep_ms(update_interval)
    pwm.duty_u16(0)

def advanced_siren(duration_ms=500, start_freq=800, end_freq=1600):
    """
    اجرای افکت سایرن پیشرفته با تغییر نمایی فرکانس
    duration_ms: مدت زمان کل افکت (میلی‌ثانیه)
    start_freq: فرکانس شروع (هرتز)
    end_freq: فرکانس پایان (هرتز)
    """
    steps = 30  # تعداد گام‌های تغییر
    # افزایش فرکانس به صورت نمایی
    for i in range(steps):
        # محاسبه فرکانس با استفاده از تغییر نمایی
        freq = int(start_freq * ((end_freq / start_freq) ** (i / steps)))
        pwm.freq(freq)
        pwm.duty_u16(35000)
        utime.sleep_ms(duration_ms // (2 * steps))
    # کاهش فرکانس به صورت نمایی
    for i in range(steps):
        freq = int(end_freq * ((start_freq / end_freq) ** (i / steps)))
        pwm.freq(freq)
        pwm.duty_u16(35000)
        utime.sleep_ms(duration_ms // (2 * steps))
    pwm.duty_u16(0)

def advanced_alarm():
    """
    اجرای یک الگوی هشدار حرفه‌ای با استفاده از الگوریتم‌های فوق پیشرفته:
      1. تون پایدار با افکت ویبراتو جهت ایجاد حس پویایی
      2. سایرن پیشرفته با تغییر نمایی فرکانس
      3. بیپ‌های تند با افکت ویبراتو جهت جلب توجه فوری
    """
    # بخش اول: تون با ویبراتو برای جلب توجه اولیه
    vibrato_tone(base_freq=1000, duration=500, vibrato_depth=70, vibrato_speed=25)
    utime.sleep_ms(50)
    # بخش دوم: سایرن پیشرفته با تغییر نمایی فرکانس
    advanced_siren(duration_ms=600, start_freq=800, end_freq=1800)
    utime.sleep_ms(50)
    # بخش سوم: چند بیپ تند با افکت ویبراتو مختصر
    for _ in range(3):
        vibrato_tone(base_freq=2000, duration=80, vibrato_depth=100, vibrato_speed=30)
        utime.sleep_ms(20)

# اجرای مداوم هشدار برای بیدارسازی سریع راننده
while True:
    advanced_alarm()
