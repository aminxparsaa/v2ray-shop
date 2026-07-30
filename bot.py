"""
V2Ray Config Shop - Telegram Bot
ربات تلگرام فروشگاه کانفیگ V2Ray
"""

import os
import json
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

# Store user orders and admin state
user_orders = {}
admin_chat_id = None
# Track which user is in "upload config" mode
upload_mode = {}


def get_github_headers():
    """هدر GitHub API"""
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
        data = {
            'message': f'Delete config: {path}',
            'sha': sha
        }
        response = requests.delete(url, headers=get_github_headers(), json=data)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error deleting config: {e}")
    return False


def upload_config_to_github(filename, content_dict):
    """آپلود کانفیگ به GitHub"""
    try:
        import base64
        url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CONFIGS_PATH}{filename}'
        content_json = json.dumps(content_dict, ensure_ascii=False, indent=2)
        content_bytes = base64.b64encode(content_json.encode('utf-8')).decode('utf-8')

        data = {
            'message': f'Add config: {filename}',
            'content': content_bytes
        }
        response = requests.put(url, headers=get_github_headers(), json=data)
        return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Error uploading config: {e}")
    return False


def get_random_configs(count=5):
    """دریافت کانفیگ‌های تصادفی"""
    configs = list_configs_from_github()
    if len(configs) >= count:
        import random
        selected = random.sample(configs, count)
    else:
        selected = configs

    result = []
    for cfg in selected:
        try:
            url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{cfg["path"]}'
            response = requests.get(url, headers=get_github_headers())
            if response.status_code == 200:
                import base64
                file_content = response.json().get('content', '')
                decoded = base64.b64decode(file_content).decode('utf-8')
                result.append({
                    'name': cfg['name'],
                    'config': json.loads(decoded)
                })
        except Exception as e:
            logger.error(f"Error getting config: {e}")
    return result


# ==================== User Commands ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /start"""
    user = update.effective_user

    # Main menu keyboard
    keyboard = [
        [KeyboardButton("🛒 خرید کانفیگ"), KeyboardButton("📦 پیگیری سفارش")],
        [KeyboardButton("📋 لیست کانفیگ‌ها"), KeyboardButton("ℹ️ راهنما")],
        [KeyboardButton("💬 پشتیبانی")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

    welcome_msg = (
        f"👋 سلام {user.first_name}!\n\n"
        f"🎯 **به فروشگاه V2Ray Shop خوش آمدید**\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔹 **سرورهای پرسرعت** در سراسر جهان\n"
        f"🔹 **امنیت بالا** با رمزنگاری پیشرفته\n"
        f"🔹 **پشتیبانی ۲۴ ساعته**\n"
        f"🔹 **تحویل فوری** پس از تأیید پرداخت\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 **سایت فروشگاه:**\n"
        f"https://psi-court-essays-sleeve.trycloudflare.com"
    )
    await update.message.reply_text(welcome_msg, reply_markup=reply_markup, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /help"""
    help_msg = (
        "📖 **راهنمای استفاده از ربات\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🛒 **خرید کانفیگ**\n"
        "از سایت خرید کنید و رسید را ارسال کنید\n\n"
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
            "از سایت خرید کنید و رسید را ارسال کنید.\n"
            "🔗 https://psi-court-essays-sleeve.trycloudflare.com"
        )

    await update.message.reply_text(status_msg, parse_mode='Markdown')


async def configs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /configs - لیست کانفیگ‌ها"""
    configs = list_configs_from_github()

    if configs:
        msg = "📋 **لیست کانفیگ‌های موجود:**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, cfg in enumerate(configs, 1):
            msg += f"**{i}.** `{cfg['name']}`\n"
        msg += f"\n━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"\n📊 تعداد کل: **{len(configs)}** کانفیگ"
        msg += f"\n🛒 برای خرید از سایت دیدن کنید"
    else:
        msg = "📋 **لیست کانفیگ‌ها**\n\nهنوز کانفیگی اضافه نشده است."

    await update.message.reply_text(msg, parse_mode='Markdown')


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پشتیبانی"""
    await update.message.reply_text(
        "💬 **پشتیبانی**\n\n"
        "برای ارتباط با پشتیبانی:\n"
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
        "پشتیبانی در اسرع وقت رسید شما را بررسی می‌کند.\n"
        "پس از تأیید، **۵ کانفیگ V2Ray** برای شما ارسال خواهد شد.\n\n"
        "⏳ لطفاً صبر کنید...\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(confirm_msg, parse_mode='Markdown')

    # Notify admin
    if admin_chat_id:
        keyboard = [
            [
                InlineKeyboardButton("✅ تأیید و ارسال کانفیگ", callback_data=f"approve_{user.id}"),
            ],
            [
                InlineKeyboardButton("❌ رد پرداخت", callback_data=f"reject_{user.id}")
            ],
            [
                InlineKeyboardButton("📊 جزئیات کاربر", callback_data=f"details_{user.id}")
            ]
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

        # Forward the photo to admin
        await context.bot.forward_message(
            chat_id=admin_chat_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id
        )

        # Send approval buttons
        await context.bot.send_message(
            chat_id=admin_chat_id,
            text=admin_msg,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        logger.warning(f"Admin chat ID not set. Receipt from user {user.id}")


# ==================== Upload Config Mode ====================

async def handle_text_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت کانفیگ متنی در حالت آپلود"""
    user_id = update.effective_user.id

    if user_id not in upload_mode:
        return False

    text = update.message.text.strip()

    # Cancel
    if text == '❌ انصراف':
        del upload_mode[user_id]
        await update.message.reply_text(
            "❌ **آپلود کانفیگ لغو شد.**",
            parse_mode='Markdown'
        )
        return True

    # Try to parse JSON
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

    # Get filename
    filename = upload_mode[user_id].get('filename', '')

    if not filename:
        # Ask for filename
        upload_mode[user_id]['config_data'] = config_data
        upload_mode[user_id]['waiting_for_filename'] = True
        await update.message.reply_text(
            "📝 **نام فایل را وارد کنید:**\n\n"
            "مثال: `us-premium.json`\n\n"
            "⚠️ نام باید با .json تمام شود.",
            parse_mode='Markdown'
        )
        return True

    # Upload to GitHub
    success = upload_config_to_github(filename, config_data)

    del upload_mode[user_id]

    if success:
        await update.message.reply_text(
            f"✅ **کانفیگ با موفقیت آپلود شد!**\n\n"
            f"📁 فایل: `{filename}`\n"
            f"📦 مخزن: `{GITHUB_REPO}`\n\n"
            f"🔗 https://github.com/{GITHUB_REPO}/blob/main/{GITHUB_CONFIGS_PATH}{filename}",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ **خطا در آپلود کانفیگ!**\n\n"
            "لطفاً دوباره تلاش کنید.",
            parse_mode='Markdown'
        )

    return True


async def handle_text_filename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت نام فایل"""
    user_id = update.effective_user.id

    if user_id not in upload_mode or not upload_mode[user_id].get('waiting_for_filename'):
        return False

    filename = update.message.text.strip()

    # Validate filename
    if not filename.endswith('.json'):
        await update.message.reply_text(
            "❌ **نام فایل باید با .json تمام شود!**\n\n"
            "مثال: `us-premium.json`",
            parse_mode='Markdown'
        )
        return True

    # Upload to GitHub
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
        await update.message.reply_text(
            "❌ **خطا در آپلود کانفیگ!**\n\n"
            "لطفاً دوباره تلاش کنید.",
            parse_mode='Markdown'
        )

    return True


# ==================== Admin Commands ====================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پنل مدیریت ادمین"""
    user_id = update.effective_user.id

    # Check if user is admin (you can set specific admin IDs)
    admin_ids = os.getenv('TELEGRAM_ADMIN_IDS', '').split(',')
    admin_ids = [int(x.strip()) for x in admin_ids if x.strip().isdigit()]

    # If no admin IDs set, first user to /setadmin is the admin
    if not admin_ids and user_id != admin_chat_id:
        await update.message.reply_text(
            "⛔ **دسترسی غیرمجاز!**\n\n"
            "فقط ادمین می‌تواند از این بخش استفاده کند.\n"
            "ابتدا /setadmin را ارسال کنید.",
            parse_mode='Markdown'
        )
        return

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
    """لیست کانفیگ‌ها برای ادمین"""
    configs = list_configs_from_github()

    if configs:
        msg = "📋 **لیست کانفیگ‌های مخزن:**\n\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for i, cfg in enumerate(configs, 1):
            msg += f"**{i}.** `{cfg['name']}`\n"
            msg += f"   📁 `{cfg['path']}`\n"
            msg += f"   📦 حجم: {cfg['size']} بایت\n\n"
        msg += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        msg += f"📊 تعداد کل: **{len(configs)}** کانفیگ\n\n"
        msg += "برای حذف از دکمه **🗑️ حذف کانفیگ** استفاده کنید."
    else:
        msg = "📋 **لیست کانفیگ‌ها**\n\nهنوز کانفیگی در مخزن وجود ندارد."

    await update.message.reply_text(msg, parse_mode='Markdown')


async def admin_delete_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """حذف کانفیگ - نمایش لیست"""
    configs = list_configs_from_github()

    if not configs:
        await update.message.reply_text(
            "🗑️ **حذف کانفیگ**\n\nهنوز کانفیگی وجود ندارد.",
            parse_mode='Markdown'
        )
        return

    # Create inline keyboard with configs
    keyboard = []
    for cfg in configs:
        keyboard.append([
            InlineKeyboardButton(
                f"🗑️ {cfg['name']}",
                callback_data=f"delcfg_{cfg['sha']}_{cfg['name']}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("❌ انصراف", callback_data="cancel_delete")
    ])

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
        "کانفیگ V2Ray را به صورت JSON ارسال کنید.\n\n"
        "**فرمت مورد نظر:**\n"
        "```json\n"
        "{\n"
        '  "name": "نام کانفیگ",\n'
        '  "description": "توضیحات",\n'
        '  "config": { ... },\n'
        '  "price": 50000,\n'
        '  "duration_days": 30,\n'
        '  "server_location": "آمریکا",\n'
        '  "stock": 10\n'
        "}\n"
        "```\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "❌ برای انصراف دکمه زیر را بزنید.",
        parse_mode='Markdown'
    )

    # Set upload mode
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
                text=f"✅ **کانفیگ حذف شد!**\n\n"
                     f"📁 فایل: `{name}`\n"
                     f"📦 مخزن: `{GITHUB_REPO}`",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(
                text="❌ **خطا در حذف کانفیگ!**\n\nلطفاً دوباره تلاش کنید.",
                parse_mode='Markdown'
            )
        return

    # Cancel delete
    if data == 'cancel_delete':
        await query.edit_message_text(
            "❌ **حذف کانفیگ لغو شد.**",
            parse_mode='Markdown'
        )
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
        # Approve payment and send configs
        if user_id in user_orders:
            user_orders[user_id]['status'] = 'approved'

            # Get 5 random configs
            configs = get_random_configs(5)

            if configs:
                # Send configs to user
                config_msg = (
                    "🎉 **پرداخت شما تأیید شد!**\n\n"
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📦 **{len(configs)} کانفیگ V2Ray برای شما ارسال شد:**\n\n"
                )

                for i, cfg in enumerate(configs, 1):
                    config_text = json.dumps(cfg['config'], ensure_ascii=False)
                    config_msg += f"**{i}. {cfg['name']}**\n"
                    config_msg += f"```\n{config_text}\n```\n\n"

                config_msg += (
                    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    "📌 **نحوه استفاده:**\n"
                    "1. اپلیکیشن V2Ray را نصب کنید\n"
                    "2. هر کانفیگ را وارد کنید\n"
                    "3. اتصال را فعال کنید\n"
                    "4. از اینترنت آزاد لذت ببرید! 🚀\n\n"
                    "💬 **پشتیبانی:** @leili9772r"
                )

                # Split message if too long (Telegram limit is 4096 chars)
                if len(config_msg) > 4000:
                    # Send configs one by one
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="🎉 **پرداخت شما تأیید شد!**\n\n📦 کانفیگ‌های شما:",
                        parse_mode='Markdown'
                    )
                    for cfg in configs:
                        config_text = json.dumps(cfg['config'], ensure_ascii=False)
                        cfg_msg = f"**{cfg['name']}**\n```\n{config_text}\n```"
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=cfg_msg,
                            parse_mode='Markdown'
                        )
                else:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=config_msg,
                        parse_mode='Markdown'
                    )

                # Update admin
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
                await query.edit_message_text(
                    text="❌ **خطا:** کانفیگی برای ارسال موجود نیست.",
                    parse_mode='Markdown'
                )
        else:
            await query.edit_message_text("❌ سفارش یافت نشد.")

    elif action == 'reject':
        # Reject payment
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
        # Show order details
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

    if not admin_chat_id:
        admin_chat_id = update.effective_chat.id
        await update.message.reply_text(
            f"✅ **ادمین تنظیم شد!**\n\n"
            f"آیدی چت: `{admin_chat_id}`\n\n"
            f"از این به بعد تمام رسیدها به این چت ارسال می‌شوند.\n"
            f"برای ورود به پنل مدیریت: /admin",
            parse_mode='Markdown'
        )
        logger.info(f"Admin chat ID set: {admin_chat_id}")
    else:
        await update.message.reply_text(
            f"ℹ️ **ادمین قبلاً تنظیم شده است.**\n\n"
            f"آیدی فعلی: `{admin_chat_id}`",
            parse_mode='Markdown'
        )


# ==================== Handle Text Messages ====================

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پردازش پیام‌های متنی"""
    text = update.message.text

    if not text:
        return

    # Check if user is in upload mode
    user_id = update.effective_user.id
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
            "🔗 https://psi-court-essays-sleeve.trycloudflare.com",
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

    elif text == "📊 آمار سایت":
        await admin_stats(update, context)

    elif text == "📋 لیست کانفیگ‌ها":
        await admin_list_configs(update, context)

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
    # Create application
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

    # Start the bot
    print("🤖 ربات تلگرام شروع به کار کرد...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
