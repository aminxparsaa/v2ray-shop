#!/bin/bash
# V2Ray Shop - Oracle Cloud Deployment Script
# اسکریپت استقرار در Oracle Cloud Free Tier

set -e

echo "🚀 V2Ray Shop - Oracle Cloud Deployment"
echo "========================================"

# ۱. آپدیت سیستم
echo "📦 Updating system..."
sudo apt update && sudo apt upgrade -y

# ۲. نصب Python
echo "🐍 Installing Python..."
sudo apt install -y python3 python3-pip python3-venv

# ۳. نصب Git
echo "📦 Installing Git..."
sudo apt install -y git

# ۴. کلون کردن پروژه
echo "📥 Cloning project..."
cd /opt
sudo git clone https://github.com/aminxparsaa/v2ray-shop.git
sudo git clone https://github.com/aminxparsaa/v2ray-configs.git

# ۵. تنظیم دسترسی
echo "🔧 Setting permissions..."
sudo chown -R $USER:$USER /opt/v2ray-shop
sudo chrown -R $USER:$USER /opt/v2ray-configs

# ۶. نصب dependencyها
echo "📚 Installing dependencies..."
cd /opt/v2ray-shop
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install python-telegram-bot

# ۷. تنظیم .env
echo "⚙️ Setting up environment..."
if [ ! -f .env ]; then
    echo "Please create .env file with:"
    echo "GITHUB_TOKEN=your_token"
    echo "GITHUB_REPO=aminxparsaa/v2ray-configs"
    echo "TELEGRAM_BOT_TOKEN=your_bot_token"
fi

# ۸. ایجاد systemd services
echo "🔧 Creating systemd services..."

# Flask Server
sudo tee /etc/systemd/system/v2ray-web.service > /dev/null <<EOF
[Unit]
Description=V2Ray Shop Website
After=network.target

[Service]
User=$USER
WorkingDirectory=/opt/v2ray-shop
ExecStart=/opt/v2ray-shop/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Telegram Bot
sudo tee /etc/systemd/system/v2ray-bot.service > /dev/null <<EOF
[Unit]
Description=V2Ray Shop Telegram Bot
After=network.target

[Service]
User=$USER
WorkingDirectory=/opt/v2ray-shop
ExecStart=/opt/v2ray-shop/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# ۹.فعال‌سازی سرویس‌ها
echo "🚀 Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable v2ray-web
sudo systemctl enable v2ray-bot
sudo systemctl start v2ray-web
sudo systemctl start v2ray-bot

# ۱۰. نصب Nginx (برای دامنه اختصاصی)
echo "🌐 Installing Nginx..."
sudo apt install -y nginx

# ۱۱. تنظیم Nginx
sudo tee /etc/nginx/sites-available/v2ray-shop > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/v2ray-shop /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "✅ Deployment Complete!"
echo "======================"
echo ""
echo "📊 Services Status:"
sudo systemctl status v2ray-web --no-pager
sudo systemctl status v2ray-bot --no-pager
echo ""
echo "🌐 Website: http://your-server-ip"
echo "🤖 Bot: @V2rayshopiran_bot"
echo ""
echo "📝 Commands:"
echo "  sudo systemctl status v2ray-web    # Check website"
echo "  sudo systemctl status v2ray-bot    # Check bot"
echo "  sudo systemctl restart v2ray-web   # Restart website"
echo "  sudo systemctl restart v2ray-bot   # Restart bot"
echo "  sudo journalctl -u v2ray-web -f    # View logs"
