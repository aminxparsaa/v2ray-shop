"""
V2Ray Config Shop - Telegram Bot
ربات تلگرام فروشگاه کانفیگ V2Ray
"""

import os
import json
import base64
import logging
import requests
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from dotenv import load_dotenv

load_dotenv()

# Bot Token
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8842107364:AAGsjw_r78ztWvLEWW_hVmqPJ2hB5E6aTcc')

# GitHub Settings
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_REPO = os.getenv('GITHUB_REPO', 'aminxparsaa/v2ray-configs')
GITHUB_CONFIGS_PATH = os.getenv('GITHUB_CONFIGS_PATH', 'configs/')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Store user orders
user_orders = {}
upload_mode = {}
pending_payment = {}

# Discount codes - only for admin/support
VALID_DISCOUNT_CODES = {
    'aminlore': 100  # 100% discount
}

# Admin and support user IDs (can use discount codes)
ADMIN_USER_IDS = [8083781285]  # Add your Telegram user ID here
SUPPORT_USER_IDS = []  # Add support user IDs if needed

# Track users waiting for discount code input
waiting_discount_code = {}

# Admin chat ID - load from file
ADMIN_FILE = '/data/workspace/v2ray-shop/.admin_chat_id'

def get_admin_chat_id():
    """خواندن آیدی ادمین از فایل"""
    try:
        if os.path.exists(ADMIN_FILE):
            with open(ADMIN_FILE, 'r') as f:
                return int(f.read().strip())
    except Exception as e:
        logger.error(f"Error reading admin ID: {e}")
    return None

def set_admin_chat_id(chat_id):
    """ذخیره آیدی ادمین در فایل"""
    try:
        with open(ADMIN_FILE, 'w') as f:
            f.write(str(chat_id))
        logger.info(f"Admin chat ID saved: {chat_id}")
    except Exception as e:
        logger.error(f"Error saving admin ID: {e}")

# Load admin ID on startup
admin_chat_id = get_admin_chat_id()
if admin_chat_id:
    logger.info(f"Admin chat ID loaded: {admin_chat_id}")


def get_github_headers():
    return {'Authorization': f'token {GITHUB_TOKEN}'}


def list_configs_from_github():
    """لیست کانفیگ‌ها از GitHub"""
    try:
        url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CONFIGS_PATH}'
        response = requests.get(url, headers=get_github_headers())
        if response.status_code == 200:
            files = response.json()
            configs = []
            for f in files:
                if f['name'].endswith('.json'):
                    configs.append({
                        'name': f['name'],
                        'path': f['path'],
                        'sha': f['sha'],
                        'size': f.get('size', 0)
                    })
            return configs
    except Exception as e:
        logger.error(f"Error listing configs: {e}")
    return []


def delete_config_from_github(path, sha):
    """حذف کانفیگ از GitHub"""
    try:
        url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{path}'
        data = {'message': f'Delete config: {path}', 'sha': sha}
        response = requests.delete(url, headers=get_github_headers(), json=data)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error deleting config: {e}")
    return False


def upload_config_to_github(filename, content_dict):
    """آپلود کانفیگ به GitHub"""
    try:
        url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CONFIGS_PATH}{filename}'
        content_json = json.dumps(content_dict, ensure_ascii=False, indent=2)
        content_bytes = base64.b64encode(content_json.encode('utf-8')).decode('utf-8')
        data = {'message': f'Add config: {filename}', 'content': content_bytes}
        response = requests.put(url, headers=get_github_headers(), json=data)
        return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Error uploading config: {e}")
    return False


# Round-robin state file
ROUND_ROBIN_FILE = '/data/workspace/v2ray-shop/.round_robin_index'

def get_round_robin_index():
    """خواندن ایندکس چرخشی"""
    try:
        if os.path.exists(ROUND_ROBIN_FILE):
            with open(ROUND_ROBIN_FILE, 'r') as f:
                return int(f.read().strip())
    except:
        pass
    return 0

def set_round_robin_index(index):
    """ذخیره ایندکس چرخشی"""
    try:
        with open(ROUND_ROBIN_FILE, 'w') as f:
            f.write(str(index))
    except Exception as e:
        logger.error(f"Error saving round-robin index: {e}")

def get_mixed_configs(count_vless=3, count_trojan=3):
    """دریافت کانفیگ‌های ترکیبی (VLESS + Trojan)"""
    configs = list_configs_from_github()
    if not configs:
        return []
    
    # Separate configs by protocol
    vless_configs = [c for c in configs if 'vless' in c['name'].lower()]
    trojan_configs = [c for c in configs if 'trojan' in c['name'].lower()]
    
    result = []
    
    # Get VLESS configs
    index = get_round_robin_index()
    for i in range(min(count_vless, len(vless_configs))):
        idx = (index + i) % len(vless_configs)
        cfg = vless_configs[idx]
        try:
            url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{cfg["path"]}'
            response = requests.get(url, headers=get_github_headers())
            if response.status_code == 200:
                file_content = response.json().get('content', '')
                decoded = base64.b64decode(file_content).decode('utf-8')
                result.append({
                    'name': cfg['name'],
                    'config': json.loads(decoded),
                    'protocol': 'vless'
                })
        except Exception as e:
            logger.error(f"Error getting config: {e}")
    
    # Get Trojan configs
    for i in range(min(count_trojan, len(trojan_configs))):
        idx = (index + i) % len(trojan_configs)
        cfg = trojan_configs[idx]
        try:
            url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{cfg["path"]}'
            response = requests.get(url, headers=get_github_headers())
            if response.status_code == 200:
                file_content = response.json().get('content', '')
                decoded = base64.b64decode(file_content).decode('utf-8')
                result.append({
                    'name': cfg['name'],
                    'config': json.loads(decoded),
                    'protocol': 'trojan'
                })
        except Exception as e:
            logger.error(f"Error getting config: {e}")
    
    # Update index for next user
    set_round_robin_index((index + 1) % max(len(vless_configs), len(trojan_configs), 1))
    
    return result


def get_next_config():
    """دریافت کانفیگ بعدی به صورت چرخشی"""
    configs = list_configs_from_github()
    if not configs:
        return None
    
    index = get_round_robin_index()
    config = configs[index % len(configs)]
    
    # Update index for next user
    set_round_robin_index((index + 1) % len(configs))
    
    # Fetch config content
    try:
        url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{config["path"]}'
        response = requests.get(url, headers=get_github_headers())
        if response.status_code == 200:
            file_content = response.json().get('content', '')
            decoded = base64.b64decode(file_content).decode('utf-8')
            return {
                'name': config['name'],
                'config': json.loads(decoded)
            }
    except Exception as e:
        logger.error(f"Error getting config: {e}")
    return None


def get_random_configs(count=1):
    """دریافت کانفیگ‌های تصادفی (edge case)"""
    configs = list_configs_from_github()
    if not configs:
        return []
    
    # Use round-robin
    result = []
    for _ in range(min(count, len(configs))):
        cfg = get_next_config()
        if cfg:
            result.append(cfg)
    return result


def config_to_share_link(config_data):
    """تبدیل کانفیگ به لینک اشتراک (vmess/vless/trojan)"""
    try:
        outbounds = config_data.get('config', config_data).get('outbounds', [])
        protocol = config_data.get('type', '')

        for outbound in outbounds:
            proto = outbound.get('protocol', protocol)

            # ==================== VMESS ====================
            if proto == 'vmess':
                vmess_obj = {
                    'v': '2',
                    'ps': config_data.get('name', 'V2Ray Config'),
                    'add': outbound['settings']['vnext'][0]['address'],
                    'port': str(outbound['settings']['vnext'][0]['port']),
                    'id': outbound['settings']['vnext'][0]['users'][0]['id'],
                    'aid': str(outbound['settings']['vnext'][0]['users'][0].get('alterId', 0)),
                    'net': outbound.get('streamSettings', {}).get('network', 'tcp'),
                    'type': 'none',
                    'host': '',
                    'path': '',
                    'tls': ''
                }
                stream = outbound.get('streamSettings', {})
                if stream.get('security') == 'tls':
                    vmess_obj['tls'] = 'tls'
                if stream.get('network') == 'ws':
                    ws = stream.get('wsSettings', {})
                    vmess_obj['path'] = ws.get('path', '')
                    vmess_obj['host'] = ws.get('headers', {}).get('Host', '')
                vmess_json = json.dumps(vmess_obj, ensure_ascii=False)
                vmess_b64 = base64.b64encode(vmess_json.encode('utf-8')).decode('utf-8')
                return f"vmess://{vmess_b64}", 'vmess'

            # ==================== VLESS ====================
            elif proto == 'vless':
                from urllib.parse import quote
                vnext = outbound['settings']['vnext'][0]
                user = vnext['users'][0]
                stream = outbound.get('streamSettings', {})
                net = stream.get('network', 'tcp')
                security = stream.get('security', 'none')

                params = {
                    'type': net,
                    'security': security,
                    'encryption': user.get('encryption', 'none')
                }

                if net == 'ws':
                    ws = stream.get('wsSettings', {})
                    path = ws.get('path', '')
                    host = ws.get('host', '') or ws.get('headers', {}).get('Host', '')
                    if path:
                        params['path'] = path
                    if host:
                        params['host'] = host

                if security == 'tls':
                    tls = stream.get('tlsSettings', {})
                    sni = tls.get('serverName', '')
                    if sni:
                        params['sni'] = sni
                        params['fp'] = 'chrome'

                query = '&'.join([f"{k}={quote(str(v), safe='')}" for k, v in params.items()])
                name = config_data.get('name', 'V2Ray Config')
                link = f"vless://{user['id']}@{vnext['address']}:{vnext['port']}?{query}#{name}"
                return link, 'vless'

            # ==================== TROJAN ====================
            elif proto == 'trojan':
                servers = outbound['settings'].get('servers', [])
                if servers:
                    server = servers[0]
                    stream = outbound.get('streamSettings', {})
                    net = stream.get('network', 'tcp')
                    security = stream.get('security', 'tls')

                    params = {'type': net}

                    if net == 'ws':
                        ws = stream.get('wsSettings', {})
                        path = ws.get('path', '')
                        host = ws.get('host', '') or ws.get('headers', {}).get('Host', '')
                        if path:
                            params['path'] = path
                        if host:
                            params['host'] = host

                    if security == 'tls':
                        tls = stream.get('tlsSettings', {})
                        sni = tls.get('serverName', '')
                        if sni:
                            params['sni'] = sni

                    # URL encode password and params
                    from urllib.parse import quote
                    password = quote(server['password'], safe='')
                    query = '&'.join([f"{k}={quote(str(v), safe='')}" for k, v in params.items()])
                    name = config_data.get('name', 'V2Ray Config')
                    link = f"trojan://{password}@{server['address']}:{server['port']}?{query}#{name}"
                    return link, 'trojan'

    except Exception as e:
        logger.error(f"Error converting config to link: {e}")
    return None, None


# ==================== User Commands ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    user = update.effective_user
    args = context.args

    keyboard = [
        [KeyboardButton("🛒 خرید کانفیگ"), KeyboardButton("📦 پیگیری سفارش")],
        [KeyboardButton("📋 لیست کانفیگ‌ها"), KeyboardButton("🎁 کد تخفیف")],
        [KeyboardButton("ℹ️ راهنما"), KeyboardButton("💬 پشتیبانی")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    # Check if coming from payment page
    if args and args[0].startswith('pay_'):
        try:
            order_id = int(args[0].split('_')[1])
            pending_payment[user.id] = {
                'order_id': order_id,
                'step': 'waiting_image'
            }

            welcome_msg = (
                f"👋 سلام {user.first_name}!\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"📸 **رسید پرداخت خود را ارسال کنید**\n\n"
                f"🔹 تصویر رسید واریزی را اینجا ارسال کنید\n"
                f"🔹 پس از تأیید، کانفیگ‌ها برای شما ارسال می‌شود\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━"
            )
            await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')
            return
        except (IndexError, ValueError):
            pass

    welcome_msg = (
        f"👋 سلام {user.first_name}!\n\n"
        f"🎯 **به فروشگاه V2Ray Shop خوش آمدید**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔹 **سرورهای پرسرعت** در سراسر جهان\n"
        f"🔹 **امنیت بالا** با رمزنگاری پیشرفته\n"
        f"🔹 **پشتیبانی ۲۴ ساعته**\n"
        f"🔹 **تحویل فوری** پس از تأیید پرداخت\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📸 **برای خرید:**\n"
        f"۱. از سایت خرید کنید\n"
        f"۲. تصویر رسید واریزی را اینجا ارسال کنید\n"
        f"۳. منتظر تأیید باشید\n\n"
        f"🔗 **سایت فروشگاه:**\n"
        f"https://psi-court-essays-sleeve.trycloudflare.com"
    )
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /help"""
    help_msg = (
        "📖 **راهنمای استفاده از ربات**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📸 **ارسال رسید**\n"
        "تصویر رسید واریزی را مستقیماً ارسال کنید\n\n"
        "📦 **پیگیری سفارش**\n"
        "وضعیت سفارش خود را بررسی کنید\n\n"
        "📋 **لیست کانفیگ‌ها**\n"
        "کانفیگ‌های موجود را مشاهده کنید\n\n"
        "💬 **پشتیبانی**\n"
        "ارتباط با پشتیبانی @leili9772r\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⚙️ **دستورات:**\n"
        "🔹 /start - منوی اصلی\n"
        "🔹 /help - راهنما\n"
        "🔹 /status - وضعیت سفارش\n"
        "🔹 /configs - لیست کانفیگ‌ها\n"
        "🔹 /admin - پنل مدیریت (فقط ادمین)"
    )
    await update.message.reply_text(help_msg, parse_mode='Markdown')


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /status"""
    user_id = update.effective_user.id

    if user_id in user_orders:
        order = user_orders[user_id]
        status_emoji = "⏳" if order['status'] == 'pending' else "✅"
        status_text = "در انتظار تأیید" if order['status'] == 'pending' else "تأیید شده"

        status_msg = (
            f"📦 **وضعیت سفارش شما**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🔹 شماره سفارش: **#{order['order_id']}**\n"
            f"🔹 مبلغ: **{order['amount']:,} تومان**\n"
            f"🔹 وضعیت: {status_emoji} **{status_text}**\n"
            f"🔹 تاریخ: {order['date']}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        status_msg = (
            "📦 **وضعیت سفارش**\n\n"
            "شما هنوز سفارشی ثبت نکرده‌اید.\n\n"
            "📸 تصویر رسید واریزی را ارسال کنید."
        )

    await update.message.reply_text(status_msg, parse_mode='Markdown')


async def configs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لیست کانفیگ‌ها"""
    configs = list_configs_from_github()

    if configs:
        msg = "📋 **لیست کانفیگ‌های موجود:**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, cfg in enumerate(configs, 1):
            msg += f"**{i}.** `{cfg['name']}`\n"
        msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"\n📊 تعداد کل: **{len(configs)}** کانفیگ"
        msg += f"\n🛒 برای خرید، رسید واریزی را ارسال کنید"
    else:
        msg = "📋 **لیست کانفیگ‌ها**\n\nهنوز کانفیگی اضافه نشده است."

    await update.message.reply_text(msg, parse_mode='Markdown')


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پشتیبانی"""
    await update.message.reply_text(
        "💬 **پشتیبانی**\n\n"
        "🔹 تلگرام: @leili9772r\n"
        "🔹 ربات: @V2rayshopiran_bot",
        parse_mode='Markdown'
    )


# ==================== Photo Handler (Receipt) ====================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت تصویر رسید"""
    global admin_chat_id

    user = update.effective_user
    photo = update.message.photo[-1]

    # Store order info
    user_orders[user.id] = {
        'user_id': user.id,
        'username': user.username or user.first_name,
        'first_name': user.first_name,
        'photo_file_id': photo.file_id,
        'status': 'pending',
        'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'message_id': update.message.message_id
    }

    # Confirm to user
    confirm_msg = (
        "✅ **رسید پرداخت دریافت شد!**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "⏳ **لطفاً صبر کنید...**\n\n"
        "پشتیبانی در اسرع وقت رسید شما را بررسی می‌کند.\n"
        "پس از تأیید، **۶ کانفیگ** (۳ VLESS + ۳ Trojan) برای شما ارسال خواهد شد.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(confirm_msg, parse_mode='Markdown')

    # Notify admin
    if admin_chat_id:
        keyboard = [
            [InlineKeyboardButton("✅ تأیید و ارسال کانفیگ", callback_data=f"approve_{user.id}")],
            [InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_{user.id}")],
            [InlineKeyboardButton("📊 جزئیات کاربر", callback_data=f"details_{user.id}")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        admin_msg = (
            f"🔔 **رسید جدید دریافت شد!**\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 **نام:** {user.first_name}\n"
            f"🆔 **یوزرنیم:** @{user.username or 'ندارد'}\n"
            f"🔢 **آیدی تلگرام:** `{user.id}`\n"
            f"📅 **تاریخ:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

        await context.bot.forward_message(
            chat_id=admin_chat_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )

        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=admin_msg,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        logger.warning(f"Admin chat ID not set. Receipt from user {user.id}")
        await update.message.reply_text(
            "⚠️ **پشتیبانی هنوز تنظیم نشده است.**\n\n"
            "لطفاً با @leili9772r تماس بگیرید.",
            parse_mode='Markdown'
        )


# ==================== Upload Config Mode ====================

async def handle_text_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت کانفیگ متنی در حالت آپلود"""
    user_id = update.effective_user.id

    if user_id not in upload_mode:
        return False

    text = update.message.text.strip()

    if text == '❌ انصراف':
        del upload_mode[user_id]
        await update.message.reply_text("❌ **آپلود کانفیگ لغو شد.**", parse_mode='Markdown')
        return True

    try:
        config_data = json.loads(text)
    except json.JSONDecodeError:
        await update.message.reply_text(
            "❌ **فرمت JSON نامعتبر است!**\n\n"
            "لطفاً کانفیگ را به صورت JSON ارسال کنید.\n"
            "برای انصراف دکمه زیر را بزنید.",
            parse_mode='Markdown'
        )
        return True

    filename = upload_mode[user_id].get('filename', '')

    if not filename:
        upload_mode[user_id]['config_data'] = config_data
        upload_mode[user_id]['waiting_for_filename'] = True
        await update.message.reply_text(
            "📝 **نام فایل را وارد کنید:**\n\n"
            "مثال: `us-vless.json`\n\n"
            "⚠️ نام باید با .json تمام شود.",
            parse_mode='Markdown'
        )
        return True

    success = upload_config_to_github(filename, config_data)
    del upload_mode[user_id]

    if success:
        await update.message.reply_text(
            f"✅ **کانفیگ با موفقیت آپلود شد!**\n\n"
            f"📁 فایل: `{filename}`\n"
            f"📦 مخزن: `{GITHUB_REPO}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ **خطا در آپلود کانفیگ!**", parse_mode='Markdown')

    return True


async def handle_text_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت نام فایل"""
    user_id = update.effective_user.id

    if user_id not in upload_mode or not upload_mode[user_id].get('waiting_for_filename'):
        return False

    filename = update.message.text.strip()

    if not filename.endswith('.json'):
        await update.message.reply_text(
            "❌ **نام فایل باید با .json تمام شود!**\n\nمثال: `us-vless.json`",
            parse_mode='Markdown'
        )
        return True

    config_data = upload_mode[user_id]['config_data']
    success = upload_config_to_github(filename, config_data)
    del upload_mode[user_id]

    if success:
        await update.message.reply_text(
            f"✅ **کانفیگ با موفقیت آپلود شد!**\n\n"
            f"📁 فایل: `{filename}`\n"
            f"📦 مخزن: `{GITHUB_REPO}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ **خطا در آپلود کانفیگ!**", parse_mode='Markdown')

    return True


# ==================== Admin Commands ====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل مدیریت ادمین"""
    keyboard = [
        [KeyboardButton("📊 آمار سایت"), KeyboardButton("📋 لیست کانفیگ‌ها")],
        [KeyboardButton("⬆️ آپلود کانفیگ"), KeyboardButton("🗑️ حذف کانفیگ")],
        [KeyboardButton("🔄 همگام‌سازی با سایت"), KeyboardButton("🏠 بازگشت به منوی اصلی")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    admin_msg = (
        "🔧 **پنل مدیریت**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "📊 **آمار** - مشاهده آمار سایت\n"
        "📋 **لیست کانفیگ‌ها** - مشاهده کانفیگ‌های موجود\n"
        "⬆️ **آپلود** - اضافه کردن کانفیگ جدید\n"
        "🗑️ **حذف** - حذف کانفیگ از مخزن\n"
        "🔄 **همگام‌سازی** - آپدیت کانفیگ‌ها در سایت\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    await update.message.reply_text(admin_msg, reply_markup=reply_markup, parse_mode='Markdown')


async def admin_list_configs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لیست کانفیگ‌ها"""
    configs = list_configs_from_github()

    if configs:
        msg = "📋 **لیست کانفیگ‌های مخزن:**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, cfg in enumerate(configs, 1):
            msg += f"**{i}.** `{cfg['name']}`\n"
            msg += f"   📁 `{cfg['path']}`\n\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📊 تعداد کل: **{len(configs)}** کانفیگ"
    else:
        msg = "📋 **لیست کانفیگ‌ها**\n\nهنوز کانفیگی در مخزن وجود ندارد."

    await update.message.reply_text(msg, parse_mode='Markdown')


async def admin_delete_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف کانفیگ"""
    configs = list_configs_from_github()

    if not configs:
        await update.message.reply_text("🗑️ **حذف کانفیگ**\n\nهنوز کانفیگی وجود ندارد.", parse_mode='Markdown')
        return

    keyboard = []
    for cfg in configs:
        keyboard.append([
            InlineKeyboardButton(f"🗑️ {cfg['name']}", callback_data=f"delcfg_{cfg['sha']}_{cfg['name']}")
        ])
    keyboard.append([InlineKeyboardButton("❌ انصراف", callback_data="cancel_delete")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🗑️ **کانفیگ مورد نظر برای حذف را انتخاب کنید:**\n\n━━━━━━━━━━━━━━━━━━━━━━",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def admin_upload_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آپلود کانفیگ جدید"""
    user_id = update.effective_user.id

    await update.message.reply_text(
        "⬆️ **آپلود کانفیگ جدید**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "کانفیگ را به صورت JSON ارسال کنید.\n\n"
        "**پروتکل‌های پشتیبانی شده:**\n"
        "🔵 VMess\n"
        "🟢 VLESS\n"
        "🔴 Trojan\n\n"
        "**فرمت مورد نظر:**\n"
        "```json\n"
        "{\n"
        '  "name": "نام کانفیگ",\n'
        '  "description": "توضیحات",\n'
        '  "type": "vless",\n'
        '  "config": {\n'
        '    "inbounds": [...],\n'
        '    "outbounds": [...]\n'
        "  },\n"
        '  "price": 50000,\n'
        '  "stock": 10\n'
        "}\n"
        "```\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ برای انصراف دکمه **❌ انصراف** را بزنید.",
        parse_mode='Markdown'
    )

    upload_mode[user_id] = {'mode': 'upload', 'waiting_for_filename': False}


async def admin_sync(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """همگام‌سازی با سایت"""
    await update.message.reply_text(
        "🔄 **همگام‌سازی با سایت**\n\n"
        "برای همگام‌سازی کانفیگ‌ها با سایت:\n\n"
        "1. به پنل مدیریت سایت بروید\n"
        "2. دکمه **همگام‌سازی با GitHub** را بزنید\n\n"
        f"🔗 https://psi-court-essays-sleeve.trycloudflare.com/admin",
        parse_mode='Markdown'
    )


async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """آمار سایت"""
    configs = list_configs_from_github()

    stats_msg = (
        "📊 **آمار سایت**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📦 **تعداد کانفیگ‌ها:** {len(configs)}\n"
        f"📁 **مخزن GitHub:** `{GITHUB_REPO}`\n"
        f"🔗 **لینک سایت:** psi-court-essays-sleeve.trycloudflare.com\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )

    await update.message.reply_text(stats_msg, parse_mode='Markdown')


# ==================== Callback Handlers ====================

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش دکمه‌های inline"""
    global admin_chat_id

    query = update.callback_query
    await query.answer()

    data = query.data

    # Delete config callback
    if data.startswith('delcfg_'):
        parts = data.split('_', 2)
        sha = parts[1]
        name = parts[2]

        success = delete_config_from_github(f'{GITHUB_CONFIGS_PATH}{name}', sha)

        if success:
            await query.edit_message_text(
                text=f"✅ **کانفیگ حذف شد!**\n\n📁 فایل: `{name}`",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ **خطا در حذف کانفیگ!**", parse_mode='Markdown')
        return

    if data == 'cancel_delete':
        await query.edit_message_text("❌ **حذف کانفیگ لغو شد.**", parse_mode='Markdown')
        return

    # Approve/Reject payment
    if '_' not in data:
        return

    action, user_id_str = data.split('_', 1)

    try:
        user_id = int(user_id_str)
    except ValueError:
        return

    if action == 'approve':
        if user_id in user_orders:
            user_orders[user_id]['status'] = 'approved'

            configs = get_mixed_configs(count_vless=3, count_trojan=3)

            if configs:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🎉 **پرداخت شما تأیید شد!**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n📦 **کانفیگ‌های شما:**",
                    parse_mode='Markdown'
                )

                for i, cfg in enumerate(configs, 1):
                    share_link, proto_type = config_to_share_link(cfg['config'])

                    proto_emoji = {'vmess': '🔵', 'vless': '🟢', 'trojan': '🔴'}
                    emoji = proto_emoji.get(proto_type, '⚪')
                    cfg_header = f"{emoji} **{i}. {cfg['name']}**"
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=cfg_header,
                        parse_mode='Markdown'
                    )

                    if share_link:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=f"```\n{share_link}\n```",
                            parse_mode='Markdown'
                        )

                final_msg = (
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "✅ **تمام کانفیگ‌ها ارسال شد!**\n\n"
                    "📌 **نحوه استفاده:**\n"
                    "۱. لینک بالا را **کپی** کنید\n"
                    "۲. اپلیکیشن V2Ray را باز کنید\n"
                    "۳. روی **+** بزنید\n"
                    "۴. **Import from Clipboard** را انتخاب کنید\n"
                    "۵. اتصال را فعال کنید 🚀\n\n"
                    "💬 **پشتیبانی:** @leili9772r\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━"
                )
                await context.bot.send_message(
                    chat_id=user_id,
                    text=final_msg,
                    parse_mode='Markdown'
                )

                await query.edit_message_text(
                    text=f"✅ **پرداخت تأیید شد!**\n\n"
                         f"📦 {len(configs)} کانفیگ برای کاربر "
                         f"{user_orders[user_id]['first_name']} ارسال شد.",
                    parse_mode='Markdown'
                )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="⚠️ **خطا:** کانفیگی برای ارسال موجود نیست.\n"
                         "لطفاً با پشتیبانی تماس بگیرید: @leili9772r",
                    parse_mode='Markdown'
                )
        else:
            await query.edit_message_text("❌ سفارش یافت نشد.")

    elif action == 'reject':
        if user_id in user_orders:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ **پرداخت شما تأیید نشد.**\n\n"
                     "لطفاً با پشتیبانی تماس بگیرید: @leili9772r",
                parse_mode='Markdown'
            )

            await query.edit_message_text(
                text=f"❌ **پرداخت رد شد**\n\n"
                     f"به کاربر {user_orders[user_id]['first_name']} اطلاع داده شد.",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("❌ سفارش یافت نشد.")

    elif action == 'details':
        if user_id in user_orders:
            order = user_orders[user_id]
            details_msg = (
                f"📊 **جزئیات سفارش:**\n\n"
                f"👤 نام: {order['first_name']}\n"
                f"🆔 یوزرنیم: @{order['username']}\n"
                f"🆔 آیدی تلگرام: {order['user_id']}\n"
                f"📅 تاریخ: {order['date']}\n"
                f"📝 وضعیت: {order['status']}"
            )
            await query.answer(text=details_msg, show_alert=True)
        else:
            await query.answer(text="اطلاعاتی موجود نیست.", show_alert=True)


# ==================== Set Admin ====================

async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تنظیم ادمین"""
    global admin_chat_id

    chat_id = update.effective_chat.id

    if not admin_chat_id:
        admin_chat_id = chat_id
        set_admin_chat_id(chat_id)  # Save to file
        await update.message.reply_text(
            f"✅ **ادمین تنظیم شد!**\n\n"
            f"آیدی چت: `{chat_id}`\n\n"
            f"از این به بعد تمام رسیدها به این چت ارسال می‌شوند.\n"
            f"برای ورود به پنل مدیریت: /admin",
            parse_mode='Markdown'
        )
    else:
        # Allow re-setting admin
        admin_chat_id = chat_id
        set_admin_chat_id(chat_id)
        await update.message.reply_text(
            f"✅ **ادمین آپدیت شد!**\n\n"
            f"آیدی جدید: `{chat_id}`",
            parse_mode='Markdown'
        )


# ==================== Handle Text Messages ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های متنی"""
    text = update.message.text

    if not text:
        return

    user_id = update.effective_user.id

    # Check if user is waiting for discount code
    if user_id in waiting_discount_code:
        if waiting_discount_code[user_id]:
            del waiting_discount_code[user_id]
            
            # Validate discount code
            code = text.strip().lower()
            if code in VALID_DISCOUNT_CODES:
                discount = VALID_DISCOUNT_CODES[code]
                # Send free config
                cfg = get_next_config()
                if cfg:
                    share_link, proto_type = config_to_share_link(cfg['config'])
                    proto_emoji = {'vmess': '🔵', 'vless': '🟢', 'trojan': '🔴'}
                    emoji = proto_emoji.get(proto_type, '⚪')
                    
                    await update.message.reply_text(
                        f"✅ **کد تخفیف فعال شد!**\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"🎁 **تخفیف {discount}%**\n\n"
                        f"📦 **کانفیگ رایگان شما:**\n",
                        parse_mode='Markdown'
                    )
                    
                    await update.message.reply_text(
                        f"{emoji} **{cfg['name']}**",
                        parse_mode='Markdown'
                    )
                    
                    if share_link:
                        await update.message.reply_text(
                            f"```\n{share_link}\n```",
                            parse_mode='Markdown'
                        )
                    
                    await update.message.reply_text(
                        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "📌 **نحوه استفاده:**\n"
                        "۱. لینک بالا را **کپی** کنید\n"
                        "۲. اپلیکیشن V2Ray را باز کنید\n"
                        "۳. روی **+** بزنید\n"
                        "۴. **Import from Clipboard** را انتخاب کنید\n"
                        "۵. اتصال را فعال کنید 🚀\n\n"
                        "💬 **پشتیبانی:** @leili9772r\n\n"
                        "━━━━━━━━━━━━━━━━━━━━━━",
                        parse_mode='Markdown'
                    )
                else:
                    await update.message.reply_text(
                        "⚠️ **خطا:** کانفیگی برای ارسال موجود نیست.\n"
                        "لطفاً با پشتیبانی تماس بگیرید: @leili9772r",
                        parse_mode='Markdown'
                    )
            else:
                await update.message.reply_text(
                    "❌ **کد تخفیف نامعتبر است!**\n\n"
                    "لطفاً کد صحیح را وارد کنید.",
                    parse_mode='Markdown'
                )
            return True
        else:
            return False

    # Check if user is in upload mode
    if user_id in upload_mode:
        if upload_mode[user_id].get('waiting_for_filename'):
            await handle_text_filename(update, context)
        else:
            await handle_text_upload(update, context)
        return

    # Menu buttons
    if text == "🛒 خرید کانفیگ":
        await update.message.reply_text(
            "🛒 **خرید کانفیگ**\n\n"
            "برای خرید کانفیگ به سایت مراجعه کنید:\n"
            "🔗 https://psi-court-essays-sleeve.trycloudflare.com\n\n"
            "📸 پس از پرداخت، تصویر رسید را اینجا ارسال کنید.",
            parse_mode='Markdown'
        )
    elif text == "📦 پیگیری سفارش":
        await status_command(update, context)
    elif text == "📋 لیست کانفیگ‌ها":
        await configs_command(update, context)
    elif text == "ℹ️ راهنما":
        await help_command(update, context)
    elif text == "💬 پشتیبانی":
        await support_command(update, context)
    elif text == "🎁 کد تخفیف":
        waiting_discount_code[user_id] = True
        await update.message.reply_text(
            "🎁 **کد تخفیف**\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "کد تخفیف خود را وارد کنید:\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )
    elif text == "📊 آمار سایت":
        await admin_stats(update, context)
    elif text == "⬆️ آپلود کانفیگ":
        await admin_upload_config(update, context)
    elif text == "🗑️ حذف کانفیگ":
        await admin_delete_config(update, context)
    elif text == "🔄 همگام‌سازی با سایت":
        await admin_sync(update, context)
    elif text == "🏠 بازگشت به منوی اصلی":
        await start(update, context)


# ==================== Main ====================

def main():
    """اجرای ربات"""
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("configs", configs_command))
    application.add_handler(CommandHandler("setadmin", set_admin))
    application.add_handler(CommandHandler("admin", admin_panel))

    # Handle photos (receipts)
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Handle callback buttons
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Handle text messages (menu)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 ربات تلگرام شروع به کار کرد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
