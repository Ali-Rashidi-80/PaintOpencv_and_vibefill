const translations = {
    fa: {
        siteTitle: "استریم نقاشی دیجیتال",
        navHome: "خانه",
        navAbout: "درباره ما",
        navGallery: "گالری",
        navContact: "تماس با ما",
        footerAbout: "درباره ما",
        footerAboutText: "ما در استریم نقاشی دیجیتال، با ترکیب هنر و فناوری، بستری خلاقانه برای خلق آثار دیجیتال فراهم کرده‌ایم. هدف ما، ارتقای تجربه هنری شماست.",
        footerLinks: "لینک‌های مفید",
        footerTerms: "شرایط و قوانین",
        footerConnect: "با ما در ارتباط باشید",
        footerCopyright: "© 2025 استریم نقاشی دیجیتال. تمامی حقوق محفوظ است.",
        introHeading: "معرفی سیستم",
        introText: `
        <p>کاربر گرامی، به <strong>جهان خلاقیت دیجیتال</strong> خوش آمدید! پلتفرم پیشرفته نقاشی دیجیتال ما، دروازه‌ای به سوی تجربه‌ای بی‌نظیر از <em>هنر و فناوری</em> است.</p>
        <p>با بهره‌گیری از <strong>کنترل دقیق سرووها</strong>، <strong>استریم زنده با کیفیت بالا</strong> و <strong>اتصال لحظه‌ای وب‌سوکت</strong>، این سیستم شما را به خلق آثار هنری بی‌مانند دعوت می‌کند. کافیست رنگ دلخواه خود را انتخاب کنید و با حرکات انگشت، شاهکارهایی خلاقانه بر بوم دیجیتال بیافرینید.</p>
        <p>طراحی شده بر پایه چارچوب <em>Flask</em> و فناوری <em>WebSocket</em>، این پلتفرم تغییرات رنگ و موقعیت سرووها را در <strong>لحظه</strong> به نمایش می‌گذارد. با تنظیمات حرفه‌ای دوربین و سروو، زوایا را به دلخواه تغییر دهید و از <em>نمای زنده</em> لذت ببرید.</p>
        <p>گالری تصاویر ما با فناوری <em>AJAX</em> به‌صورت خودکار به‌روزرسانی می‌شود تا آثار جدید شما در لحظه به نمایش درآیند، بدون نیاز به بارگذاری مجدد.</p>
        <p>ما در تلاشیم تا با ارائه محیطی <strong>پویا</strong>، <strong>تعاملی</strong> و <strong>کاربرپسند</strong>، خلاقیت شما را در دنیای هنر دیجیتال به اوج برسانیم.</p>
        `,
        cameraControl: "کنترل دوربین و سرووها",
        axisX: "محور X",
        axisY: "محور Y",
        incrementalAdjustment: "تنظیم تدریجی (5 درجه)",
        send: "ارسال",
        gallery: "گالری تصاویر",
        prevImages: "تصاویر قدیمی‌تر",
        nextImages: "تصاویر جدیدتر",
        viewImage: "نمایش تصویر",
        download: "دانلود",
        deleteImage: "حذف تصویر",
        close: "بستن",
        colorSelectLabel: "انتخاب رنگ برای نقاشی:",
        sendColor: "ارسال رنگ",
        actionSelectLabel: "اقدامات نقاشی:",
        sendAction: "ارسال اقدام",
        langLabel: "English",
        themeLight: "حالت روز",
        themeDark: "حالت شب",
        liveStream: "استریم زنده",
        startStream: "شروع استریم",
        stopStream: "قطع استریم",
        colorSelection: "انتخاب رنگ",
        paintingActions: "اقدامات نقاشی",
        servoControl: "کنترل سرووها",
        incrementXPlus: "X +5°",
        incrementXMinus: "X -5°",
        incrementYPlus: "Y +5°",
        incrementYMinus: "Y -5°",
        colorRed: "قرمز",
        colorCrimson: "زرشکی",
        colorOrange: "نارنجی",
        colorGreen: "سبز",
        colorYellow: "زرد",
        colorPurple: "بنفش",
        colorBrown: "قهوه‌ای",
        colorPink: "صورتی",
        colorBlue: "آبی",
        colorCyan: "فیروزه‌ای",
        colorMagenta: "ارغوانی",
        colorWhite: "سفید",
        colorGray: "خاکستری",
        colorLightBlue: "آبی روشن",
        colorDarkBlue: "آبی تیره",
        colorLightGreen: "سبز روشن",
        colorDarkGreen: "سبز تیره",
        colorOlive: "زیتونی",
        colorTeal: "سبزآبی",
        colorViolet: "نیلی",
        colorGold: "طلایی",
        colorSilver: "نقره‌ای",
        actionEraser: "پاک‌کن",
        actionSavePainting: "ذخیره نقاشی",
        actionNextDesign: "طرح بعدی",
        actionPreviousDesign: "طرح قبلی",
        actionResetChanges: "بازنشانی تغییرات",
        actionUndo: "عقب‌گرد",
        connectionError: "خطا در اتصال",
        angleError: "زاویه‌ها باید بین 0 تا 180 باشند.",
        colorError: "خطا در ارسال رنگ",
        actionError: "خطا در ارسال اقدام",
        galleryError: "خطا در بارگذاری گالری",
        deleteError: "خطا در حذف تصویر",
        colorChanged: "رنگ تغییر یافت: ",
        actionPerformed: "اقدام انجام شد: ",
        colorReceived: "رنگ از سرور دریافت شد: ",
        actionReceived: "اقدام از سرور دریافت شد: ",
        desktopMode: "حالت دسکتاپ",
        mobileMode: "حالت موبایل"
    },
    en: {
        siteTitle: "Digital Painting Stream",
        navHome: "Home",
        navAbout: "About Us",
        navGallery: "Gallery",
        navContact: "Contact Us",
        footerAbout: "About Us",
        footerAboutText: "At Digital Painting Stream, we combine art and technology to provide a creative platform for crafting digital masterpieces. Our goal is to elevate your artistic experience.",
        footerLinks: "Useful Links",
        footerTerms: "Terms & Conditions",
        footerConnect: "Connect With Us",
        footerCopyright: "© 2025 Digital Painting Stream. All rights reserved.",
        introHeading: "System Introduction",
        introText: `
        <p>Welcome, dear user, to the <strong>world of digital creativity</strong>! Our advanced digital painting platform is your gateway to an unparalleled experience of <em>art and technology</em>.</p>
        <p>Powered by <strong>precise servo control</strong>, <strong>high-quality live streaming</strong>, and <strong>real-time WebSocket connectivity</strong>, this system invites you to create extraordinary artworks. Simply select your desired color and, with the touch of your finger, craft masterpieces on a digital canvas.</p>
        <p>Built on the <em>Flask</em> framework and <em>WebSocket</em> technology, our platform displays color changes and servo adjustments in <strong>real time</strong>. With professional camera and servo settings, customize angles to your preference and enjoy a <em>live view</em>.</p>
        <p>Our image gallery, powered by <em>AJAX</em>, automatically updates to showcase your latest creations instantly, without requiring a page reload.</p>
        <p>We strive to deliver a <strong>dynamic</strong>, <strong>interactive</strong>, and <strong>user-friendly</strong> environment that elevates your creativity to new heights in the realm of digital art.</p>
        `,
        cameraControl: "Camera & Servo Control",
        axisX: "Axis X",
        axisY: "Axis Y",
        incrementalAdjustment: "Incremental Adjustment (5°)",
        send: "Send",
        gallery: "Image Gallery",
        prevImages: "Older Images",
        nextImages: "Newer Images",
        viewImage: "View Image",
        download: "Download",
        deleteImage: "Delete Image",
        close: "Close",
        colorSelectLabel: "Select color for painting:",
        sendColor: "Send Color",
        actionSelectLabel: "Painting actions:",
        sendAction: "Send Action",
        langLabel: "فارسی",
        themeLight: "Light",
        themeDark: "Dark",
        liveStream: "Live Stream",
        startStream: "Start Stream",
        stopStream: "Stop Stream",
        colorSelection: "Color Selection",
        paintingActions: "Painting Actions",
        servoControl: "Servo Control",
        incrementXPlus: "X +5°",
        incrementXMinus: "X -5°",
        incrementYPlus: "Y +5°",
        incrementYMinus: "Y -5°",
        colorRed: "Red",
        colorCrimson: "Crimson",
        colorOrange: "Orange",
        colorGreen: "Green",
        colorYellow: "Yellow",
        colorPurple: "Purple",
        colorBrown: "Brown",
        colorPink: "Pink",
        colorBlue: "Blue",
        colorCyan: "Cyan",
        colorMagenta: "Magenta",
        colorWhite: "White",
        colorGray: "Gray",
        colorLightBlue: "Light Blue",
        colorDarkBlue: "Dark Blue",
        colorLightGreen: "Light Green",
        colorDarkGreen: "Dark Green",
        colorOlive: "Olive",
        colorTeal: "Teal",
        colorViolet: "Violet",
        colorGold: "Gold",
        colorSilver: "Silver",
        actionEraser: "Eraser",
        actionSavePainting: "Save Painting",
        actionNextDesign: "Next Design",
        actionPreviousDesign: "Previous Design",
        actionResetChanges: "Reset Changes",
        actionUndo: "Undo",
        connectionError: "Connection error",
        angleError: "Angles must be between 0 and 180.",
        colorError: "Error sending color",
        actionError: "Error sending action",
        galleryError: "Error loading gallery",
        deleteError: "Error deleting image",
        colorChanged: "Color changed: ",
        actionPerformed: "Action performed: ",
        colorReceived: "Color received: ",
        actionReceived: "Action received: ",
        desktopMode: "Desktop Mode",
        mobileMode: "Mobile Mode"
    }
};

let currentLang = localStorage.getItem('language') || 'fa';
let currentPage = parseInt(localStorage.getItem('galleryPage')) || 0;
let currentDeviceMode = localStorage.getItem('deviceMode') || 'desktop';
const imagesPerPage = 6;
let ws;
let isStreaming = false;

function debounce(func, wait) {
    let timeout;
    return function (...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function showNotification(message, type = 'success') {
    const container = document.getElementById('notificationContainer');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="close-btn">×</button>
    `;
    container.appendChild(notification);
    setTimeout(() => notification.classList.add('show'), 100);
    const closeBtn = notification.querySelector('.close-btn');
    closeBtn.onclick = () => notification.remove();
    setTimeout(() => notification.remove(), 5000);
}

function updateLanguage() {
    try {
        document.documentElement.lang = currentLang;
        document.title = translations[currentLang].siteTitle;
        document.body.classList.remove('lang-fa', 'lang-en');
        document.body.classList.add(`lang-${currentLang}`);

        document.querySelectorAll("[data-key]").forEach(el => {
            const key = el.getAttribute("data-key");
            if (translations[currentLang][key]) {
                if (el.tagName === 'BUTTON' || el.tagName === 'A') {
                    const icon = el.querySelector('i');
                    const textSpan = el.querySelector('span');
                    if (key === 'langLabel' || key === 'themeLight' || key === 'themeDark') {
                        el.setAttribute('aria-label', translations[currentLang][key]);
                    } else if (textSpan) {
                        textSpan.innerHTML = translations[currentLang][key];
                    } else {
                        el.innerHTML = icon ? `<i class="${icon.className}"></i><span>${translations[currentLang][key]}</span>` : translations[currentLang][key];
                    }
                } else {
                    el.innerHTML = translations[currentLang][key];
                }
            }
        });

        ['colorSelect', 'actionSelect'].forEach(selectId => {
            const select = document.getElementById(selectId);
            Array.from(select.options).forEach(option => {
                const key = option.getAttribute('data-key');
                if (key && translations[currentLang][key]) {
                    option.text = translations[currentLang][key];
                }
            });
        });

        const streamBtnText = document.getElementById('streamBtnText');
        streamBtnText.innerText = isStreaming ? translations[currentLang].stopStream : translations[currentLang].startStream;
        document.getElementById('toggleStreamBtn').setAttribute('aria-label', translations[currentLang][isStreaming ? 'stopStream' : 'startStream']);
        document.getElementById('langToggle').setAttribute('aria-label', translations[currentLang].langLabel);
        document.getElementById('themeToggle').setAttribute('aria-label', translations[currentLang][document.body.classList.contains('dark-mode') ? 'themeLight' : 'themeDark']);
        updateDeviceModeButton();
    } catch (err) {
        console.error("Error in updateLanguage:", err);
        showNotification(translations[currentLang].connectionError, 'danger');
    }
}

function updateDeviceModeButton() {
    try {
        const deviceModeBtnText = document.getElementById('deviceModeText');
        const deviceModeToggle = document.getElementById('deviceModeToggle');
        if (!deviceModeBtnText || !deviceModeToggle) {
            console.error("Device mode elements not found");
            return;
        }
        const isMobileMode = currentDeviceMode === 'mobile';
        deviceModeBtnText.innerText = translations[currentLang][isMobileMode ? 'desktopMode' : 'mobileMode'];
        deviceModeToggle.setAttribute('aria-label', translations[currentLang][isMobileMode ? 'desktopMode' : 'mobileMode']);
        const icon = deviceModeToggle.querySelector('i');
        icon.className = isMobileMode ? 'fas fa-desktop me-2' : 'fas fa-mobile-alt me-2';
    } catch (err) {
        console.error("Error in updateDeviceModeButton:", err);
        showNotification("خطا در به‌روزرسانی دکمه حالت دستگاه", 'danger');
    }
}

const sendDeviceMode = debounce(() => {
    try {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ device_mode: currentDeviceMode }));
            showNotification(`${translations[currentLang][currentDeviceMode + 'Mode']} ${translations[currentLang].actionPerformed}`, 'success');
        } else {
            showNotification(translations[currentLang].connectionError, 'danger');
        }
    } catch (err) {
        console.error("Error in sendDeviceMode:", err);
        showNotification(translations[currentLang].connectionError, 'danger');
    }
}, 300);

document.getElementById('langToggle').onclick = () => {
    currentLang = currentLang === 'fa' ? 'en' : 'fa';
    localStorage.setItem('language', currentLang);
    updateLanguage();
};

const themeToggle = document.getElementById('themeToggle');
const themeIcon = document.getElementById('themeIcon');
themeToggle.onclick = () => {
    const isDarkMode = document.body.classList.contains('dark-mode');
    document.body.classList.toggle('dark-mode', !isDarkMode);
    document.body.classList.toggle('light-mode', isDarkMode);
    themeIcon.className = isDarkMode ? "fas fa-sun" : "fas fa-moon";
    localStorage.setItem('theme', isDarkMode ? 'light' : 'dark');
    document.getElementById('themeToggle').setAttribute('aria-label', translations[currentLang][isDarkMode ? 'themeDark' : 'themeLight']);
};

const storedTheme = localStorage.getItem('theme') || 'dark';
document.body.classList.remove('light-mode', 'dark-mode');
document.body.classList.add(storedTheme === 'dark' ? 'dark-mode' : 'light-mode');
themeIcon.className = storedTheme === 'dark' ? "fas fa-moon" : "fas fa-sun";

let lastScrollTop = 0;
window.addEventListener('scroll', () => {
    const header = document.querySelector('.main-header');
    const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
    if (currentScroll > lastScrollTop && currentScroll > 100) {
        header.classList.add('hidden');
    } else {
        header.classList.remove('hidden');
    }
    lastScrollTop = currentScroll <= 0 ? 0 : currentScroll;
});

const menuToggle = document.querySelector('.menu-toggle');
const headerNav = document.querySelector('.header-nav');
menuToggle.addEventListener('click', () => {
    headerNav.classList.toggle('active');
    const isExpanded = headerNav.classList.contains('active');
    menuToggle.setAttribute('aria-expanded', isExpanded);
    menuToggle.querySelector('i').className = isExpanded ? 'fas fa-times' : 'fas fa-bars';
});

document.querySelectorAll('.header-nav a').forEach(link => {
    link.addEventListener('click', () => {
        headerNav.classList.remove('active');
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.querySelector('i').className = 'fas fa-bars';
    });
});

document.addEventListener('click', (e) => {
    if (!headerNav.contains(e.target) && !menuToggle.contains(e.target)) {
        headerNav.classList.remove('active');
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.querySelector('i').className = 'fas fa-bars';
    }
});

const servoXSlider = document.getElementById('servoX');
const servoYSlider = document.getElementById('servoY');
const servoXNumber = document.getElementById('servoXNumber');
const servoYNumber = document.getElementById('servoYNumber');
const servoXValue = document.getElementById('servoXValue');
const servoYValue = document.getElementById('servoYValue');

const storedColor = localStorage.getItem('selectedColor');
if (storedColor) document.getElementById('colorSelect').value = storedColor;
const storedAction = localStorage.getItem('selectedAction');
if (storedAction) document.getElementById('actionSelect').value = storedAction;
const storedServoX = localStorage.getItem('servoX');
const storedServoY = localStorage.getItem('servoY');
if (storedServoX) {
    servoXSlider.value = servoXNumber.value = servoXValue.innerText = storedServoX;
}
if (storedServoY) {
    servoYSlider.value = servoYNumber.value = servoYValue.innerText = storedServoY;
}

servoXSlider.oninput = () => {
    servoXValue.innerText = servoXNumber.value = servoXSlider.value;
    localStorage.setItem('servoX', servoXSlider.value);
};
servoYSlider.oninput = () => {
    servoYValue.innerText = servoYNumber.value = servoYSlider.value;
    localStorage.setItem('servoY', servoYSlider.value);
};
servoXNumber.oninput = () => {
    servoXValue.innerText = servoXSlider.value = servoXNumber.value;
    localStorage.setItem('servoX', servoXNumber.value);
};
servoYNumber.oninput = () => {
    servoYValue.innerText = servoYSlider.value = servoYNumber.value;
    localStorage.setItem('servoY', servoYNumber.value);
};

document.getElementById('actionSelect').onchange = () => {
    localStorage.setItem('selectedAction', document.getElementById('actionSelect').value);
};

async function adjustAngle(axis, delta) {
    let slider, numberInput, valueSpan;
    if (axis === 'X') {
        slider = servoXSlider;
        numberInput = servoXNumber;
        valueSpan = servoXValue;
    } else {
        slider = servoYSlider;
        numberInput = servoYNumber;
        valueSpan = servoYValue;
    }
    let currentValue = parseInt(slider.value);
    let newValue = Math.max(0, Math.min(180, currentValue + delta));
    slider.value = numberInput.value = valueSpan.innerText = newValue;
    localStorage.setItem('servo' + axis, newValue);
    const data = { servoX: servoXSlider.value, servoY: servoYSlider.value };
    try {
        const response = await fetch('/set_servo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        showNotification(result.message, result.status === 'success' ? 'success' : 'danger');
    } catch (err) {
        showNotification(translations[currentLang].connectionError, 'danger');
    }
}

document.getElementById('servoForm').onsubmit = async (e) => {
    e.preventDefault();
    const data = { servoX: servoXSlider.value, servoY: servoYSlider.value };
    if (data.servoX < 0 || data.servoX > 180 || data.servoY < 0 || data.servoY > 180) {
        showNotification(translations[currentLang].angleError, 'danger');
        return;
    }
    try {
        const response = await fetch('/set_servo', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        showNotification(result.message, result.status === 'success' ? 'success' : 'danger');
    } catch (err) {
        showNotification(translations[currentLang].connectionError, 'danger');
    }
};

document.getElementById('sendColorBtn').onclick = async () => {
    const colorSelect = document.getElementById('colorSelect');
    let selectedColor = colorSelect.value;
    localStorage.setItem('selectedColor', selectedColor);
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ color: selectedColor }));
        showNotification(`${translations[currentLang].colorChanged} ${colorSelect.options[colorSelect.selectedIndex].text}`, 'success');
    } else {
        try {
            const response = await fetch('/set_color', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ color: selectedColor })
            });
            const result = await response.json();
            showNotification(result.message, result.status === 'success' ? 'success' : 'danger');
        } catch (err) {
            showNotification(translations[currentLang].colorError, 'danger');
        }
    }
};

document.getElementById('sendActionBtn').onclick = async () => {
    const actionSelect = document.getElementById('actionSelect');
    let selectedAction = actionSelect.value;
    localStorage.setItem('selectedAction', selectedAction);
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ action: selectedAction }));
        showNotification(`${translations[currentLang].actionPerformed} ${actionSelect.options[actionSelect.selectedIndex].text}`, 'success');
    } else {
        try {
            const response = await fetch('/set_action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: selectedAction })
            });
            const result = await response.json();
            showNotification(result.message, result.status === 'success' ? 'success' : 'danger');
        } catch (err) {
            showNotification(translations[currentLang].actionError, 'danger');
        }
    }
};

function initWS() {
    try {
        ws = new WebSocket("ws://services.irn9.chabokan.net:35338/ws");
        ws.onopen = () => console.log("WebSocket connection established");
        ws.onmessage = (message) => {
            try {
                const msg = JSON.parse(message.data);
                if (msg.color) {
                    document.getElementById('colorSelect').value = msg.color;
                    localStorage.setItem('selectedColor', msg.color);
                    showNotification(`${translations[currentLang].colorReceived} ${msg.color}`, 'info');
                } else if (msg.action) {
                    document.getElementById('actionSelect').value = msg.action;
                    localStorage.setItem('selectedAction', msg.action);
                    showNotification(`${translations[currentLang].actionReceived} ${msg.action}`, 'info');
                } else if (msg.device_mode) {
                    currentDeviceMode = msg.device_mode;
                    localStorage.setItem('deviceMode', currentDeviceMode);
                    updateDeviceModeButton();
                    showNotification(`${translations[currentLang][currentDeviceMode + 'Mode']} ${translations[currentLang].actionPerformed}`, 'info');
                }
            } catch (e) {
                console.error("Error processing WebSocket message:", e);
            }
        };
        ws.onclose = () => {
            console.log("WebSocket connection closed");
            setTimeout(initWS, 5000);
        };
        ws.onerror = (err) => {
            console.error("WebSocket Error:", err);
            ws.close();
        };
    } catch (err) {
        console.error("Error initializing WebSocket:", err);
    }
}

const streamPlaceholder = document.getElementById('streamPlaceholder');
const toggleStreamBtn = document.getElementById('toggleStreamBtn');
const streamBtnText = document.getElementById('streamBtnText');

function resizeStreamIframe() {
    const iframe = streamPlaceholder.querySelector('iframe');
    if (iframe) {
        const placeholderRect = streamPlaceholder.getBoundingClientRect();
        iframe.style.width = `${placeholderRect.width}px`;
        iframe.style.height = `${placeholderRect.height}px`;
    }
}

function toggleStream() {
    try {
        if (!isStreaming) {
            const streamIframe = document.createElement('iframe');
            streamIframe.src = "http://services.irn9.chabokan.net:35338/video_feed";
            streamIframe.setAttribute('frameborder', '0');
            streamIframe.setAttribute('allowfullscreen', 'true');
            streamIframe.setAttribute('title', translations[currentLang].liveStream);
            streamIframe.style.width = '100%';
            streamIframe.style.height = '100%';
            streamPlaceholder.innerHTML = '';
            streamPlaceholder.appendChild(streamIframe);
            streamPlaceholder.classList.add('active');
            streamBtnText.innerText = translations[currentLang].stopStream;
            toggleStreamBtn.setAttribute('aria-label', translations[currentLang].stopStream);
            isStreaming = true;
            setTimeout(resizeStreamIframe, 100);
        } else {
            streamPlaceholder.innerHTML = '<i class="fas fa-play"></i>';
            streamPlaceholder.classList.remove('active');
            streamBtnText.innerText = translations[currentLang].startStream;
            toggleStreamBtn.setAttribute('aria-label', translations[currentLang].startStream);
            isStreaming = false;
        }
    } catch (err) {
        console.error("Error in toggleStream:", err);
        showNotification("خطا در پخش استریم", 'danger');
    }
}

toggleStreamBtn.onclick = toggleStream;
streamPlaceholder.onclick = toggleStream;
window.addEventListener('resize', resizeStreamIframe);

document.getElementById('deviceModeToggle').onclick = async () => {
    try {
        currentDeviceMode = currentDeviceMode === 'desktop' ? 'mobile' : 'desktop';
        localStorage.setItem('deviceMode', currentDeviceMode);
        updateDeviceModeButton();
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ device_mode: currentDeviceMode }));
            showNotification(`${translations[currentLang][currentDeviceMode + 'Mode']} ${translations[currentLang].actionPerformed}`, 'success');
        } else {
            const response = await fetch('/set_device_mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ device_mode: currentDeviceMode })
            });
            const result = await response.json();
            showNotification(result.message, result.status === 'success' ? 'success' : 'danger');
        }
    } catch (err) {
        console.error("Error in deviceModeToggle:", err);
        showNotification("خطا در تغییر حالت دستگاه", 'danger');
    }
};

async function loadGallery(page = currentPage) {
    try {
        const response = await fetch(`/get_gallery?page=${page}&limit=${imagesPerPage}`);
        const data = await response.json();
        const container = document.getElementById('galleryContainer');
        container.innerHTML = "";
        data.image_urls.forEach(url => {
            const div = document.createElement('div');
            div.className = 'gallery-item';
            div.innerHTML = `<img src="${url}" alt="${translations[currentLang].digitalPaintingImage || 'Digital Painting Image'}" loading="lazy">`;
            div.onclick = () => openModal(url);
            container.appendChild(div);
        });

        const prevBtn = document.getElementById('prevImagesBtn');
        const nextBtn = document.getElementById('nextImagesBtn');
        prevBtn.classList.toggle('visible', data.has_more);
        nextBtn.classList.toggle('visible', page > 0);
    } catch (err) {
        console.error("Error loading gallery:", err);
        showNotification(translations[currentLang].galleryError, 'danger');
    }
}

document.getElementById('prevImagesBtn').onclick = () => {
    currentPage++;
    localStorage.setItem('galleryPage', currentPage);
    loadGallery(currentPage);
};

document.getElementById('nextImagesBtn').onclick = () => {
    if (currentPage > 0) {
        currentPage--;
        localStorage.setItem('galleryPage', currentPage);
        loadGallery(currentPage);
    }
};

function openModal(imageUrl) {
    document.getElementById('modalImage').src = imageUrl;
    document.getElementById('downloadBtn').href = imageUrl;
    document.getElementById('deleteBtn').setAttribute('data-filename', imageUrl.split('/').pop());
    const imageModal = new bootstrap.Modal(document.getElementById('imageModal'));
    imageModal.show();
}

document.getElementById('deleteBtn').onclick = async () => {
    const filename = document.getElementById('deleteBtn').getAttribute('data-filename');
    try {
        const response = await fetch('/delete_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        const result = await response.json();
        if (result.status === 'success') {
            showNotification(result.message, 'success');
            loadGallery(currentPage);
            const modal = bootstrap.Modal.getInstance(document.getElementById('imageModal'));
            modal.hide();
        } else {
            showNotification(result.message, 'danger');
        }
    } catch (err) {
        showNotification(translations[currentLang].deleteError, 'danger');
    }
};

window.onload = () => {
    updateLanguage();
    initWS();
    loadGallery(currentPage);
    setInterval(() => loadGallery(currentPage), 5000);
};