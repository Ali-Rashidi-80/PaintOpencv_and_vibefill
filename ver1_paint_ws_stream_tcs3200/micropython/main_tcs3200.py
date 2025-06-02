from tcs3200 import TCS3200
import utime as time, ujson as json, sys

CALIB_FILE = "calib_colors.json"
NUM_SAMPLES = 50   # تعداد نمونه هر اندازه‌گیری
ERR_THRESH = 10    # درصد خطای مجاز ±5%

# تعریف لیست رنگ‌ها با اضافه کردن "black" و "white" در ابتدای لیست
ALL_COLORS = ["black", "white", "red", "bright_orange", "orange", "green", "yellow", "purple", "brown", "pink", "blue"]

def save_calib(data):
    with open(CALIB_FILE, "w") as f:
        json.dump(data, f)

def load_calib():
    try:
        with open(CALIB_FILE, "r") as f:
            return json.load(f)
    except:
        return None

def print_progress(sample, total):
    # ایجاد نوار پیشرفت متنی 20 ک0.....................................................................................................................................................................اراکتری
    bar_length = 20
    filled = int(bar_length * sample / total)
    bar = "[" + "#" * filled + "-" * (bar_length - filled) + "]"
    sys.stdout.write("\rنمونه‌گیری: %s %d/%d" % (bar, sample, total))
    if hasattr(sys.stdout, "flush"):
        sys.stdout.flush()

def take_samples(sensor):
    filt = (sensor.RED, sensor.GREEN, sensor.BLUE, sensor.CLEAR)
    avgs = [0]*4
    for comp in range(4):
        samples = []
        for i in range(1, NUM_SAMPLES+1):
            sensor.filter = filt[comp]
            sensor.meas = sensor.ON
            while sensor._end_tick == 0:
                time.sleep_ms(5)
            samples.append(sensor.measured_freq)
            sensor._cycle = sensor._start_tick = sensor._end_tick = 0
            print_progress(i, NUM_SAMPLES)
        print()  # رفتن به خط بعد از پایان نمونه‌گیری هر کانال
        avgs[comp] = sum(samples) / NUM_SAMPLES
    return avgs

def normalize(raw, black, white):
    # نرمال کردن با استفاده از مقدار سیاه و سفید
    return [ (raw[i]-black[i])/(white[i]-black[i]) if (white[i]-black[i]) else 0 for i in range(4) ]

def calibrate_all_colors(sensor):
    calib = {}
    # کالیبراسیون برای black و white به صورت جداگانه
    input("قرار دادن هدف برای black و فشار Enter: ")
    print("در حال گرفتن نمونه‌های black:")
    raw_black = take_samples(sensor)
    calib["raw_black"] = raw_black  # ذخیره‌ی نمونه‌های خام برای black

    input("قرار دادن هدف برای white و فشار Enter: ")
    print("در حال گرفتن نمونه‌های white:")
    raw_white = take_samples(sensor)
    calib["raw_white"] = raw_white  # ذخیره‌ی نمونه‌های خام برای white

    # کالیبراسیون برای سایر رنگ‌ها با نرمال کردن نمونه‌ها
    for color in ALL_COLORS:
        if color in ["black", "white"]:
            continue
        input("قرار دادن هدف برای {} و فشار Enter: ".format(color))
        print("در حال گرفتن نمونه‌های {}:".format(color))
        samples = take_samples(sensor)
        # نرمال کردن نمونه‌ها با استفاده از raw_black و raw_white
        calib[color] = normalize(samples, raw_black, raw_white)
    save_calib(calib)
    return calib

def measure_once(sensor):
    filt = (sensor.RED, sensor.GREEN, sensor.BLUE, sensor.CLEAR)
    meas = [0]*4
    for comp in range(4):
        sensor.filter = filt[comp]
        sensor.meas = sensor.ON
        while sensor._end_tick == 0:
            time.sleep_ms(5)
        meas[comp] = sensor.measured_freq
        sensor._cycle = sensor._start_tick = sensor._end_tick = 0
    return meas

def identify_color(sensor, calib):
    # نرمال کردن مقادیر خوانده شده با استفاده از raw_black و raw_white
    norm_meas = normalize(measure_once(sensor), calib["raw_black"], calib["raw_white"])
    best, best_err, best_errs = None, 100, None
    for color in ALL_COLORS:
        # برای black و white از مقادیر ثابت استفاده می‌کنیم
        if color == "black":
            target = [0, 0, 0, 0]
        elif color == "white":
            target = [1, 1, 1, 1]
        elif color in calib:
            target = calib[color]
        else:
            continue
        # محاسبه اختلاف (به درصد) برای هر کانال
        diffs = [ (norm_meas[i] - target[i])*100 for i in range(4)]
        max_abs_err = max([abs(d) for d in diffs])
        if max_abs_err <= ERR_THRESH and max_abs_err < best_err:
            best, best_err, best_errs = color, max_abs_err, diffs
    return best, norm_meas, best_errs

def main():
    sensor = TCS3200(OUT=20, S2=18, S3=19, S0=16, S1=17, LED=23)
    sensor.debugging = False
    calib = load_calib() or calibrate_all_colors(sensor)
    while True:
        color, norm_vals, errs = identify_color(sensor, calib)
        if color:
            print("رنگ شناسایی شده: {} (حداکثر خطا: {}٪)".format(color, ERR_THRESH))
            if errs:
                print("اختلاف هر کانال (به درصد): RED: {:+.1f}، GREEN: {:+.1f}، BLUE: {:+.1f}، CLEAR: {:+.1f}".format(*errs))
        else:
            print("رنگ نامشخص. مقادیر نرمال: {}".format(norm_vals))
        time.sleep(0.5)

if __name__ == "__main__":
    main()

