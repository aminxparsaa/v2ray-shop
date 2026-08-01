#!/bin/bash
# V2Ray Shop - Keep Alive Script
# این اسکریپت سرور، ربات و تونل رو زنده نگه می‌داره

PROJECT_DIR="/data/workspace/v2ray-shop"
LOG_DIR="$PROJECT_DIR/logs"
VENV="$PROJECT_DIR/venv"

# ساخت پوشه لاگ
mkdir -p "$LOG_DIR"

echo "🚀 V2Ray Shop - Keep Alive Started"
echo "=================================="

# تابع بررسی و ری‌استارت
check_and_restart() {
    local name=$1
    local pid_file=$2
    local command=$3
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    
    echo "🔄 Restarting $name..."
    cd "$PROJECT_DIR"
    source venv/bin/activate
    nohup $command > "$LOG_DIR/${name}.log" 2>&1 &
    echo $! > "$pid_file"
    echo "✅ $name started (PID: $!)"
    return 1
}

# حلقه اصلی
while true; do
    # بررسی Flask Server
    check_and_restart "flask" "$PROJECT_DIR/.flask.pid" "python app.py"
    
    # بررسی Telegram Bot
    check_and_restart "bot" "$PROJECT_DIR/.bot.pid" "python bot.py"
    
    # بررسی Cloudflared Tunnel
    if ! pgrep -f "cloudflared" > /dev/null; then
        echo "🔄 Starting cloudflared tunnel..."
        nohup /tmp/cloudflared tunnel --url http://localhost:5000 > "$LOG_DIR/tunnel.log" 2>&1 &
        echo $! > "$PROJECT_DIR/.tunnel.pid"
        echo "✅ Tunnel started (PID: $!)"
    fi
    
    # ذخیره URL جدید تونل
    sleep 5
    TUNNEL_URL=$(grep -o 'https://[^ ]*trycloudflare.com' "$LOG_DIR/tunnel.log" 2>/dev/null | tail -1)
    if [ -n "$TUNNEL_URL" ]; then
        echo "$TUNNEL_URL" > "$PROJECT_DIR/.tunnel_url"
        echo "🌐 Tunnel URL: $TUNNEL_URL"
    fi
    
    # صبر ۳۰ ثانیه
    sleep 30
done
