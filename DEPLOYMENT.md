# 🚀 V2Ray Shop - راهنمای استقرار دائمی

## 📊 مقایسه راه‌حل‌ها

### ۱. Oracle Cloud Free Tier (پیشنهادی ⭐)
- **هزینه:** رایگان همیشه
- **منابع:** ۴ هسته ARM + ۲۴GB رم
- **ماندگاری:** ⭐⭐⭐⭐⭐
- **سختی:** متوسط

### ۲. Render.com
- **هزینه:** رایگان (محدود)
- **منابع:** 512MB رم
- **ماندگاری:** ⭐⭐⭐
- **سختی:** آسان

### ۳. Fly.io
- **هزینه:** رایگان (محدود)
- **منابع:** 256MB رم
- **ماندگاری:** ⭐⭐⭐
- **سختی:** آسان

---

## 🎯 روش ۱: Oracle Cloud (بهترین)

### مرحله ۱: ثبت‌نام
1. به [cloud.oracle.com](https://cloud.oracle.com) برید
2. حساب رایگان بسازید
3. VM ایجاد کنید:
   - **Image:** Ubuntu 22.04
   - **Shape:** VM.Standard.A1.Flex (ARM)
   - **Cores:** 4
   - **RAM:** 24GB
   - **Storage:** 200GB

### مرحله ۲: اتصال
```bash
ssh -i your-key.pem ubuntu@your-server-ip
```

### مرحله ۳: استقرار
```bash
# کلون کردن پروژه
cd /opt
sudo git clone https://github.com/aminxparsaa/v2ray-shop.git
sudo git clone https://github.com/aminxparsaa/v2ray-configs.git

# اجرای اسکریپت استقرار
cd /opt/v2ray-shop
chmod +x deploy_oracle.sh
./deploy_oracle.sh
```

### مرحله ۴: تنظیم .env
```bash
cd /opt/v2ray-shop
nano .env
```

محتوای .env:
```
GITHUB_TOKEN=your_github_token
GITHUB_REPO=aminxparsaa/v2ray-configs
TELEGRAM_BOT_TOKEN=your_bot_token
```

### مرحله ۵: ری‌استارت
```bash
sudo systemctl restart v2ray-web
sudo systemctl restart v2ray-bot
```

---

## 🎯 روش ۲: Render.com (ساده‌تر)

### مرحله ۱: ثبت‌نام
1. به [render.com](https://render.com) برید
2. حساب رایگان بسازید
3. GitHub رو 연결 کنید

### مرحله ۲: ایجاد Web Service
1. **New** → **Web Service**
2. ریپو `aminxparsaa/v2ray-shop` رو انتخاب کنید
3. تنظیمات:
   - **Name:** v2ray-shop
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py`
4. **Environment Variables** اضافه کنید:
   - `GITHUB_TOKEN`
   - `GITHUB_REPO`
   - `TELEGRAM_BOT_TOKEN`

### مرحله ۳: ایجاد Worker برای Bot
1. **New** → **Background Worker**
2. ریپو `aminxparsaa/v2ray-shop` رو انتخاب کنید
3. تنظیمات:
   - **Name:** v2ray-bot
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
4. **Environment Variables** اضافه کنید

---

## 🎯 روش ۳: Docker (محلی)

### مرحله ۱: نصب Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

### مرحله ۲: اجرا
```bash
cd /data/workspace/v2ray-shop
docker-compose up -d
```

### مرحله ۳: بررسی
```bash
docker-compose ps
docker-compose logs -f
```

---

## 🔧 دستورات مفید

### بررسی وضعیت
```bash
# Oracle Cloud
sudo systemctl status v2ray-web
sudo systemctl status v2ray-bot

# Docker
docker-compose ps
```

### ری‌استارت
```bash
# Oracle Cloud
sudo systemctl restart v2ray-web
sudo systemctl restart v2ray-bot

# Docker
docker-compose restart
```

### مشاهده لاگ‌ها
```bash
# Oracle Cloud
sudo journalctl -u v2ray-web -f
sudo journalctl -u v2ray-bot -f

# Docker
docker-compose logs -f
```

---

## ⚠️ نکات مهم

1. **توکن GitHub:** حتماً `.env` رو تنظیم کنید
2. **توکن ربات:** از `@BotFather` بگیرید
3. **فایروال:** پورت 80 و 443 رو باز کنید
4. **دامنه:** برای SSL گواهی نصب کنید
5. **بک‌آپ:** منظم دیتابیس رو بک‌آپ بگیرید

---

## 📞 پشتیبانی

- **ربات:** @V2rayshopiran_bot
- **پشتیبانی:** @leili9772r
- **GitHub:** aminxparsaa
