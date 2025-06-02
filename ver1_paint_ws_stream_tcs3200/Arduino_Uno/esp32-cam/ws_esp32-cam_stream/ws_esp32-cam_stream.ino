#include "esp_camera.h"
#include <WiFi.h>
#include <ArduinoWebsockets.h>

using namespace websockets;

// اطلاعات شبکه و سرور وب‌سوکت فلسک
const char* ssid = "SAMSUNG";
const char* password = "panzer790";
const char* websocket_server = "https://services.irn9.chabokan.net";
const uint16_t websocket_port = 5760;
const char* websocket_path = "/ws";

// پین‌های مربوط به دوربین (مدل AL-THINKER)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

WebsocketsClient client;
bool isConnected = false;  // flag برای مدیریت وضعیت اتصال

// callback برای رویدادهای وب‌سوکت
void onEventsCallback(WebsocketsEvent event, String data) {
  if (event == WebsocketsEvent::ConnectionOpened) {
    Serial.println("Connection opened");
    isConnected = true;
  } else if (event == WebsocketsEvent::ConnectionClosed) {
    Serial.println("Connection closed");
    isConnected = false;
  }
}

// تابع اتصال به وب‌سوکت
void connectWebSocket() {
  String url = String(websocket_server) + ":" + String(websocket_port) + websocket_path;
  Serial.print("Connecting to ");
  Serial.println(url);
  
  if (client.connect(websocket_server, websocket_port, websocket_path)) {
    Serial.println("WebSocket connected!");
  } else {
    Serial.println("WebSocket connection failed.");
  }
}

void setup() {
  Serial.begin(115200);
  Serial.println();

  // پیکربندی دوربین
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // تنظیم کیفیت تصویر بر اساس وجود PSRAM
  if (psramFound()) {
    // تنظیمات برای سخت‌افزار قدرتمند (PSRAM موجود)
    config.frame_size = FRAMESIZE_VGA; 
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    // تنظیمات برای سیستم‌های بدون PSRAM
    config.frame_size = FRAMESIZE_XGA; 
    config.jpeg_quality = 14;
    config.fb_count = 1;
  }

  // مقداردهی اولیه دوربین
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  // اتصال به شبکه WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.println("WiFi connected");

  // تنظیم callback برای رویدادهای وب‌سوکت
  client.onEvent(onEventsCallback);
  
  // اتصال به وب‌سوکت سرور فلسک
  connectWebSocket();
}

void loop() {
  // پردازش رویدادهای وب‌سوکت
  client.poll();

  // در صورت عدم اتصال، تلاش مجدد برای اتصال
  if (!isConnected) {
    connectWebSocket();
  }

  // گرفتن فریم از دوربین
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }

  // ارسال داده فریم (به صورت باینری) از طریق وب‌سوکت
  client.sendBinary((const char*)fb->buf, fb->len);
  esp_camera_fb_return(fb);

  delay(1); // تنظیم فاصله کوتاه جهت کاهش بار پردازشی
}
