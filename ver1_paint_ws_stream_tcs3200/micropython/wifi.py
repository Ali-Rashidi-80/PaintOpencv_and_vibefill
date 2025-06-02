# Ali Rashidi
# t.me/WriteYourway
import network
import time
import uasyncio as asyncio

# اطلاعات شبکه WiFi
ssid = "SAMSUNG"  # نام شبکه WiFi
password = "panzer790"  # رمز عبور شبکه WiFi

# مقداردهی اولیه WLAN
wlan = network.WLAN(network.STA_IF)
wlan.active(True)

# تابع بررسی وضعیت اتصال WiFi
def isconnected():
    return wlan.isconnected()

# تابع اتصال به WiFi
def connect_wifi():
    if isconnected():
        print(f"✅ Already connected. IP Address: {wlan.ifconfig()[0]}")
        return True

    print("\n🔄 Connecting to WiFi...")
    wlan.connect(SSID, PASSWORD)

    timeout = 10  # حداکثر زمان تلاش برای اتصال (ثانیه)
    start_time = time.time()

    while not isconnected():
        if time.time() - start_time > timeout:
            print("\n❌ Connection timed out!")
            return False
        print(".", end="")
        time.sleep(1)

    wifi_status()
    return True

# بررسی وضعیت WiFi
def wifi_status():
    if isconnected():
        ip, subnet, gateway, dns = wlan.ifconfig()
        print("\n📡 WiFi Info:")
        print(f"  - IP Address: {ip}")
        print(f"  - Subnet Mask: {subnet}")
        print(f"  - Gateway: {gateway}")
        print(f"  - DNS Server: {dns}")
    else:
        print("\n❌ Not connected to WiFi")

# تابع غیرهمزمان برای اطمینان از اتصال به WiFi
async def ensure_wifi():
    while not isconnected():
        print("\n⚠ WiFi lost! Reconnecting...")
        connect_wifi()
        await asyncio.sleep(2)
    print(f"\nWiFi Connected!✅. IP Address: {wlan.ifconfig()[0]}")
    return True

# تابع شروع
def start():
    # به‌جای asyncio.run، فقط تابع ensure_wifi را فراخوانی می‌کنیم
    # زیرا حلقه اصلی در cooler_control.py اجرا می‌شود
    loop = asyncio.get_event_loop()
    loop.create_task(ensure_wifi())