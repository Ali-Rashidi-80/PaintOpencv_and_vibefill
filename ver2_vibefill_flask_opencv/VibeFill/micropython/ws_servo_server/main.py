import network
import ujson
import uasyncio as asyncio
import time
import math
from machine import Pin, PWM

# تلاش برای وارد کردن کتابخانه وب‌سوکت از پوشه lib
try:
    import client as ws_client
except ImportError:
    raise ImportError("کتابخانه uwebsocket.client یافت نشد. لطفاً آن را از https://github.com/danni/uwebsockets دانلود کرده و به پوشه lib/ انتقال دهید.")

# ================================
# اتصال به WiFi
# ================================
SSID = "SAMSUNG"
PASSWORD = "panzer790"

async def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)
    print("در حال اتصال به WiFi...")
    while not wlan.isconnected():
        await asyncio.sleep(0.5)
    print("اتصال برقرار شد. IP:", wlan.ifconfig()[0])
    return wlan

# ================================
# کلاس کنترل سروو
# ================================
class ServoController:
    def __init__(self, pin_num, angle_file):
        self.angle_file = angle_file
        self.servo_pwm = PWM(Pin(pin_num))
        self.servo_pwm.freq(50)
    def save_angle(self, angle):
        try:
            with open(self.angle_file, "w") as f:
                ujson.dump({"angle": angle}, f)
        except Exception as e:
            print("⚠️ خطا در ذخیره زاویه:", e)
    def load_angle(self):
        try:
            with open(self.angle_file, "r") as f:
                data = ujson.load(f)
                angle = data.get("angle", 90)
                return max(0, min(180, angle))
        except Exception as e:
            print("⚠️ خطا در بازیابی زاویه، مقدار پیش‌فرض 90:", e)
            return 90
    def angle_to_duty(self, angle):
        MIN_DUTY = 1400
        MAX_DUTY = 8000
        return int(MIN_DUTY + (angle / 180) * (MAX_DUTY - MIN_DUTY))
    def set_angle(self, current, target):
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
            time.sleep(0.02 + 0.03 * (1 - smooth_progress))
        try:
            self.servo_pwm.duty_u16(self.angle_to_duty(target))
        except Exception as e:
            print("⚠️ خطا در تنظیم PWM:", e)
        self.save_angle(target)
        time.sleep(0.1)
        return target

# ایجاد کنترل‌کننده‌های سروو
servo1 = ServoController(pin_num=2, angle_file="servo1.json")
servo2 = ServoController(pin_num=3, angle_file="servo2.json")
current_angle1 = servo1.load_angle()
current_angle2 = servo2.load_angle()

# ================================
# اتصال به وب‌سوکت Flask
# ================================
# آدرس وب‌سوکت سرور Flask را به endpoint مناسب تغییر دهید.
WS_URL = "ws://services.fin2.chabokan.net:29434/ws"

def process_command(cmd):
    try:
        servo1_target = int(cmd.get('servo1', 90))
        servo2_target = int(cmd.get('servo2', 90))
        print("دریافت دستور: servo1 =", servo1_target, "servo2 =", servo2_target)
        global current_angle1, current_angle2
        current_angle1 = servo1.set_angle(current_angle1, servo1_target)
        current_angle2 = servo2.set_angle(current_angle2, servo2_target)
    except Exception as e:
        print("خطا در پردازش دستور:", e)

async def websocket_client():
    while True:
        try:
            print("در حال اتصال به وب‌سوکت...")
            # فراخوانی blocking به صورت مستقیم (این فراخوانی ممکن است حلقه را به مدت کوتاهی مسدود کند)
            ws = ws_client.connect(WS_URL)
            print("اتصال وب‌سوکت برقرار شد")
            while True:
                data = ws.recv()  # دریافت blocking
                if data:
                    try:
                        msg = ujson.loads(data)
                        if 'servo1' in msg and 'servo2' in msg:
                            process_command(msg)
                    except Exception as e:
                        print("خطا در پردازش پیام وب‌سوکت:", e)
                await asyncio.sleep(0.1)
        except Exception as e:
            print("خطا در اتصال وب‌سوکت:", e)
            await asyncio.sleep(5)

async def main():
    await connect_wifi()
    asyncio.create_task(websocket_client())
    while True:
        await asyncio.sleep(1)

asyncio.run(main())

