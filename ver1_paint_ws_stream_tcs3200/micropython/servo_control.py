from machine import Pin, PWM
from time import sleep
import ujson
import math

# ===============================================
# کلاس کنترل سروو برای انجام عملیات عمومی
# ===============================================
class ServoController:
    def __init__(self, pin_num, angle_file):
        """
        مقداردهی اولیه سروو: تنظیم پین PWM و فایل ذخیره زاویه.
        """
        self.angle_file = angle_file
        self.servo_pwm = PWM(Pin(pin_num))
        self.servo_pwm.freq(50)  # فرکانس استاندارد سروو (50 هرتز)
    
    def save_angle(self, angle):
        """
        ذخیره زاویه فعلی در فایل جهت جلوگیری از حرکات ناگهانی پس از ریستارت.
        """
        try:
            with open(self.angle_file, "w") as f:
                ujson.dump({"angle": angle}, f)
        except Exception as e:
            print("⚠️ خطا در ذخیره زاویه:", e)
    
    def load_angle(self):
        """
        بازیابی زاویه ذخیره شده؛ در صورت بروز خطا یا عدم وجود فایل، مقدار پیش‌فرض 90 درجه بازگردانده می‌شود.
        """
        try:
            with open(self.angle_file, "r") as f:
                data = ujson.load(f)
                angle = data.get("angle", 90)
                return max(0, min(180, angle))
        except Exception as e:
            print("⚠️ خطا در بازیابی زاویه. استفاده از مقدار پیش‌فرض 90 درجه:", e)
            return 90
    
    def angle_to_duty(self, angle):
        """
        تبدیل زاویه (0 تا 180 درجه) به مقدار duty مناسب برای PWM.
        """
        MIN_DUTY = 1400   # duty برای 0 درجه
        MAX_DUTY = 8000   # duty برای 180 درجه
        return int(MIN_DUTY + (angle / 180) * (MAX_DUTY - MIN_DUTY))
    
    def set_angle(self, current, target):
        """
        حرکت تدریجی و نرم سروو از زاویه فعلی به زاویه هدف با استفاده از منحنی سینوسی.
        همچنین هر تغییر کوچک ذخیره شده تا از حرکات ناگهانی جلوگیری شود.
        """
        # اطمینان از معتبر بودن زاویه‌ها
        current = max(0, min(180, current))
        target = max(0, min(180, target))
        
        if current == target:
            return target
        
        distance = abs(target - current)
        steps = max(1, int(distance))
        
        for i in range(1, steps + 1):
            progress = i / steps
            smooth_progress = 0.5 - 0.5 * math.cos(progress * math.pi)
            new_angle = current + (target - current) * smooth_progress
            new_angle = max(0, min(180, new_angle))
            duty = self.angle_to_duty(new_angle)
            try:
                self.servo_pwm.duty_u16(duty)
            except Exception as e:
                print("⚠️ خطا در تنظیم PWM:", e)
            self.save_angle(new_angle)
            sleep(0.02 + (0.03 * (1 - smooth_progress)))
        
        try:
            self.servo_pwm.duty_u16(self.angle_to_duty(target))
        except Exception as e:
            print("⚠️ خطا در تنظیم PWM:", e)
        self.save_angle(target)
        sleep(0.1)
        return target

# ===============================================
# ایجاد دو شیء کنترل سروو: یکی روی پین 3 و دیگری روی پین 4
# ===============================================
servo1 = ServoController(pin_num=2, angle_file="servo_angle1.json")
servo2 = ServoController(pin_num=3, angle_file="servo_angle2.json")

# ===============================================
# تابع اصلی اجرای حلقه حرکت سرووها
# ===============================================
def main_loop():
    """
    اجرای مداوم حرکت سرووها بین زوایای 90، 180 و 0 درجه.
    هر دو سروو به‌صورت همزمان حرکت می‌کنند.
    """
    current_angle1 = servo1.load_angle()
    current_angle2 = servo2.load_angle()
    print("✅ زاویه اولیه سروو 1:", current_angle1)
    print("✅ زاویه اولیه سروو 2:", current_angle2)
    
    while True:
        # حرکت به 90 درجه
        current_angle1 = servo1.set_angle(current_angle1, 20)
        current_angle2 = servo2.set_angle(current_angle2, 40)
        sleep(0.5)
        
        # حرکت به 180 درجه
        current_angle1 = servo1.set_angle(current_angle1, 90)
        current_angle2 = servo2.set_angle(current_angle2, 90)
        sleep(0.5)
        
        # حرکت به 0 درجه
        current_angle1 = servo1.set_angle(current_angle1, 0)
        current_angle2 = servo2.set_angle(current_angle2, 0)
        sleep(0.5)

# ===============================================
# اجرای کد در صورت اجرای مستقیم فایل
# ===============================================
if __name__ == "__main__":
    main_loop()
