from tcs3200 import TCS3200
import utime as time, ujson as json, sys, uasyncio as asyncio
import client as ws_client
import wifi

CALIB_FILE = "calib_colors.json"        # فایل کالیبراسیون جامع (برای رنگ‌های اضافی)
HARDWARE_CALIB_FILE = "hardware_calib.json"  # فایل کالیبراسیون سخت‌افزاری (فقط BLACK و WHITE)
NUM_SAMPLES = 50        # تعداد نمونه هر اندازه‌گیری
ERR_THRESH = 10         # درصد خطای مجاز ±10%
ALL_COLORS = ["black", "white", "red", "bright_orange", "orange", "green", "yellow", "purple", "brown", "pink", "blue"]
WS_URL = "ws://services.fin2.chabokan.net:29434/ws"  # آدرس وب‌سوکت سرور Flask

def save_calib(data):
    with open(CALIB_FILE, "w") as f:
        json.dump(data, f)

def load_calib():
    try:
        with open(CALIB_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def save_hardware_calib(data):
    with open(HARDWARE_CALIB_FILE, "w") as f:
        json.dump(data, f)

def load_hardware_calib():
    try:
        with open(HARDWARE_CALIB_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def print_progress(sample, total):
    bar_length = 20
    filled = int(bar_length * sample / total)
    bar = "[" + "#" * filled + "-" * (bar_length - filled) + "]"
    sys.stdout.write("\rنمونه‌گیری: %s %d/%d" % (bar, sample, total))
    sys.stdout.flush()

def take_samples(sensor):
    filt = (sensor.RED, sensor.GREEN, sensor.BLUE, sensor.CLEAR)
    avgs = [0] * 4
    for comp in range(4):
        samples = []
        for i in range(1, NUM_SAMPLES + 1):
            sensor.filter = filt[comp]
            sensor.meas = sensor.ON
            while sensor._end_tick == 0:
                time.sleep_ms(5)
            samples.append(sensor.measured_freq)
            sensor._cycle = sensor._start_tick = sensor._end_tick = 0
            print_progress(i, NUM_SAMPLES)
        print()
        avgs[comp] = sum(samples) / NUM_SAMPLES
    return avgs

def normalize(raw, black, white):
    return [(raw[i] - black[i]) / (white[i] - black[i]) if (white[i] - black[i]) else 0 for i in range(4)]

def calibrate_all_colors(sensor):
    """
    کالیبراسیون جامع برای رنگ‌های اضافی؛ ابتدا نمونه‌های BLACK و WHITE گرفته شده و سپس برای سایر رنگ‌ها.
    """
    calib = {}
    input("قرار دادن هدف برای BLACK و فشار Enter: ")
    print("در حال گرفتن نمونه‌های BLACK:")
    raw_black = take_samples(sensor)
    calib["raw_black"] = raw_black

    input("قرار دادن هدف برای WHITE و فشار Enter: ")
    print("در حال گرفتن نمونه‌های WHITE:")
    raw_white = take_samples(sensor)
    calib["raw_white"] = raw_white

    for color in ALL_COLORS:
        if color in ["black", "white"]:
            continue
        input("قرار دادن هدف برای {} و فشار Enter: ".format(color))
        print("در حال گرفتن نمونه‌های {}:".format(color))
        samples = take_samples(sensor)
        calib[color] = normalize(samples, raw_black, raw_white)
    save_calib(calib)
    return calib

def measure_once(sensor):
    filt = (sensor.RED, sensor.GREEN, sensor.BLUE, sensor.CLEAR)
    meas = [0] * 4
    for comp in range(4):
        sensor.filter = filt[comp]
        sensor.meas = sensor.ON
        while sensor._end_tick == 0:
            time.sleep_ms(5)
        meas[comp] = sensor.measured_freq
        sensor._cycle = sensor._start_tick = sensor._end_tick = 0
    return meas

def identify_color(sensor, calib):
    norm_meas = normalize(measure_once(sensor), calib["raw_black"], calib["raw_white"])
    best, best_err = None, 100
    for color in ALL_COLORS:
        if color == "black":
            target = [0, 0, 0, 0]
        elif color == "white":
            target = [1, 1, 1, 1]
        elif color in calib:
            target = calib[color]
        else:
            continue
        diffs = [(norm_meas[i] - target[i]) * 100 for i in range(4)]
        max_err = max([abs(d) for d in diffs])
        if max_err <= ERR_THRESH and max_err < best_err:
            best, best_err = color, max_err
    return best, norm_meas

def hardware_calibrate(sensor):
    """
    تابع کالیبراسیون سخت‌افزاری:  
    - تنظیمات اولیه (debugging، LED، تقسیم‌کننده فرکانس، تعداد چرخه) انجام می‌شود  
    - سپس متد calibrate فراخوانی شده و مقادیر BLACK و WHITE دریافت می‌شود  
    - داده‌های به‌دست آمده در قالب دیکشنری ذخیره و در فایل hardware_calib.json نوشته می‌شود.
    """
    try:
        sensor.debugging = sensor.OFF
        sensor.led = sensor.ON
        sensor.freq_divider = sensor.TWO_PERCENT
        print("تنظیم تقسیم‌کننده فرکانس:", sensor.freq_divider)
        if sensor.freq_divider == sensor.TWO_PERCENT:
            print("Frequency divider is set to 2%")
        else:
            print("Something went wrong when setting the frequency divider")
        sensor.cycles = 100
        sensor.calibrate()
        black_freq = sensor.calib(sensor.BLACK)
        print("Calibration frequencies for BLACK: ", black_freq)
        white_freq = sensor.calib(sensor.WHITE)
        print("Calibration frequencies for WHITE: ", white_freq)
        calib = {"raw_black": black_freq, "raw_white": white_freq}
        save_hardware_calib(calib)
        return calib
    except Exception as e:
        print("خطا در کالیبراسیون سخت‌افزاری:", e)
        return None

async def color_sender(sensor, calib):
    last_color = None  # رنگ قبلی ارسال شده
    # تلاش برای اتصال به وب‌سوکت
    while True:
        try:
            ws = ws_client.connect(WS_URL)
            print("اتصال وب‌سوکت برقرار شد.")
            break
        except Exception as e:
            print("خطا در اتصال به وب‌سوکت:", e)
            await asyncio.sleep(5)
    while True:
        try:
            color, norm_vals = identify_color(sensor, calib)
        except Exception as e:
            print("خطای اندازه‌گیری (مثلاً تایم‌اوت):", e)
            print("شروع مجدد کالیبراسیون سخت‌افزاری به صورت هوشمند...")
            new_calib = hardware_calibrate(sensor)
            if new_calib is not None:
                calib = new_calib
            else:
                calib = calibrate_all_colors(sensor)
            continue
        # فقط در صورت تغییر رنگ ارسال شود
        if color and color != last_color:
            msg = json.dumps({"color": color})
            try:
                ws.send(msg)
                print("ارسال رنگ:", color)
                last_color = color
            except Exception as e:
                print("خطا در ارسال پیام:", e)
        await asyncio.sleep(1)

async def main():
    sensor = TCS3200(OUT=20, S2=18, S3=19, S0=16, S1=17, LED=23)
    sensor.debugging = False

    # ابتدا تلاش می‌کنیم داده‌های کالیبراسیون سخت‌افزاری را از فایل hardware_calib.json بارگذاری کنیم.
    hw_calib = load_hardware_calib()
    if hw_calib is None:
        print("داده‌های کالیبراسیون سخت‌افزاری یافت نشد. شروع کالیبراسیون سخت‌افزاری...")
        hw_calib = hardware_calibrate(sensor)
    # سپس تلاش می‌کنیم که از این داده‌ها به عنوان پیش‌فرض استفاده کنیم؛ در صورت نیاز می‌توان آن‌ها را در کالیبراسیون جامع به کار برد.
    calib = load_calib() or calibrate_all_colors(sensor)
    # در صورت وجود داده‌های سخت‌افزاری، می‌توانیم آن‌ها را در calib درج کنیم (مثلاً مقادیر BLACK و WHITE)
    if hw_calib is not None:
        calib["raw_black"] = hw_calib.get("raw_black", calib.get("raw_black"))
        calib["raw_white"] = hw_calib.get("raw_white", calib.get("raw_white"))
        save_calib(calib)
    await color_sender(sensor, calib)

def run():
    wifi.start()
    asyncio.run(main())
    
run()    
