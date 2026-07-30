# V2Ray Shop 🛡️

فروشگاه تخصصی کانفیگ‌های V2Ray با پنل مدیریت کامل

## ✨ امکانات

- 🎨 رابط کاربری زیبا و ریسپانسیو (RTL)
- 👤 سیستم ثبت‌نام و ورود کاربران
- 📦 مدیریت کانفیگ‌ها (افزودن، ویرایش، حذف)
- 💰 قیمت‌گذاری و پرداخت
- 🔧 پنل مدیریت (ادمین) کامل
- 🐙 اتصال به GitHub برای همگام‌سازی کانفیگ‌ها
- 📊 آمار و گزارش‌گیری

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.8+
- pip

### مراحل نصب

1. **کلون کردن پروژه:**
```bash
git clone https://github.com/YOUR_USERNAME/v2ray-shop.git
cd v2ray-shop
```

2. **ایجاد محیط مجازی:**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# یا
venv\Scripts\activate  # Windows
```

3. **نصب وابستگی‌ها:**
```bash
pip install -r requirements.txt
```

4. **کپی فایل تنظیمات:**
```bash
cp .env.sample .env
```

5. **ویرایش فایل .env:**
```ini
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-password
GITHUB_TOKEN=your-github-token
GITHUB_REPO=your-username/your-repo
```

6. **ایجاد دیتابیس:**
```bash
flask init-db
```

7. **ایجاد داده‌های نمونه (اختیاری):**
```bash
flask create-sample-data
```

8. **اجرای سرور:**
```bash
flask run
```

سایت در آدرس `http://localhost:5000` قابل دسترسی است.

## 🐙 اتصال به GitHub

### ایجاد Token دسترسی

1. به Settings > Developer settings > Personal access tokens بروید
2. یک token جدید با دسترسی `repo` ایجاد کنید
3. آن را در فایل `.env` قرار دهید

### مخزن کانفیگ‌ها

یک مخزن جداگانه برای کانفیگ‌ها ایجاد کنید و فایل‌های JSON را در پوشه `configs/` قرار دهید:

```json
{
    "name": "کانفیگ VIP",
    "description": "توضیحات کانفیگ",
    "config": {
        "inbounds": [...],
        "outbounds": [...]
    },
    "price": 50000,
    "duration_days": 30,
    "server_location": "آمریکا",
    "stock": 10
}
```

### همگام‌سازی

از پنل مدیریت، دکمه "همگام‌سازی با GitHub" را بزنید تا کانفیگ‌ها خودکار دریافت شوند.

## 🚀 استقرار

### GitHub Pages

1. مخزن را روی GitHub آپلود کنید
2. در Settings > Pages، شاخه `main` را انتخاب کنید
3. GitHub Actions خودکار استقرار را انجام می‌دهد

### Render.com (توصیه شده)

1. حساب Render.com ایجاد کنید
2. مخزن را متصل کنید
3. یک **Web Service** با تنظیمات زیر ایجاد کنید:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

### Railway.app

1. حساب Railway.app ایجاد کنید
2. مخزن را متصل کنید
3. متغیرهای محیطی را تنظیم کنید

## 📁 ساختار پروژه

```
v2ray-shop/
├── app.py                  # فایل اصلی Flask
├── requirements.txt        # وابستگی‌ها
├── .env.sample             # نمونه تنظیمات
├── README.md               # راهنما
├── static/
│   ├── css/
│   │   └── style.css       # استایل‌های سفارشی
│   └── js/
│       └── main.js         # جاوااسکریپت اصلی
├── templates/
│   ├── base.html           # قالب پایه
│   ├── index.html          # صفحه اصلی
│   ├── config_detail.html  # جزئیات کانفیگ
│   ├── orders.html         # لیست سفارشات
│   ├── order_detail.html   # جزئیات سفارش
│   ├── profile.html        # پروفایل کاربر
│   ├── auth/
│   │   ├── login.html      # صفحه ورود
│   │   └── register.html   # صفحه ثبت‌نام
│   ├── admin/
│   │   ├── dashboard.html  # داشبورد مدیریت
│   │   ├── configs.html    # مدیریت کانفیگ‌ها
│   │   ├── config_form.html# فرم کانفیگ
│   │   ├── users.html      # مدیریت کاربران
│   │   └── orders.html     # مدیریت سفارشات
│   └── errors/
│       ├── 404.html        # خطای 404
│       └── 500.html        # خطای 500
└── .github/
    └── workflows/
        └── deploy.yml      # GitHub Actions
```

## 🔐 امنیت

- رمز عبورها با Werkzeug hashing ذخیره می‌شوند
- CSRF protection با Flask-WTF فعال است
- Session management امن

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/configs` | لیست کانفیگ‌ها |
| GET | `/api/config/<id>` | جزئیات کانفیگ |
| GET | `/api/order/<id>` | جزئیات سفارش |

## 🤝 مشارکت

1. Fork کنید
2. Branch جدید بسازید (`git checkout -b feature/amazing-feature`)
3. Commit کنید (`git commit -m 'Add amazing feature'`)
4. Push کنید (`git push origin feature/amazing-feature`)
5. Pull Request ایجاد کنید

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است.

## 📞 پشتیبانی

- تلگرام: @your_support
- ایمیل: support@example.com

---

**ساخته شده با ❤️ توسط Hermes Agent**
