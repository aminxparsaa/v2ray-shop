"""
V2Ray Config Shop - Flask Application
فروشگاه کانفیگ V2Ray
"""

import os
import json
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, session, abort
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///v2ray_shop.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
from models import db, User, Config, Order, SiteSettings
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'لطفا ابتدا وارد شوید'

# Import and register payment blueprint
from payment import payment_bp
app.register_blueprint(payment_bp, url_prefix='/pay')

# GitHub settings
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
GITHUB_REPO = os.getenv('GITHUB_REPO', '')
GITHUB_CONFIGS_PATH = os.getenv('GITHUB_CONFIGS_PATH', 'configs/')


# ==================== Custom Filters ====================

@app.template_filter('toLocaleString')
def to_locale_string(value):
    """Format number with comma separators"""
    try:
        return '{:,}'.format(int(value))
    except (ValueError, TypeError):
        return value


# ==================== Login Manager ====================

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ==================== Admin Decorator ====================

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('دسترسی غیرمجاز!', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== Routes ====================

@app.route('/')
def index():
    """صفحه اصلی"""
    configs = Config.query.filter_by(is_active=True).all()
    return render_template('index.html', configs=configs)


@app.route('/config/<int:config_id>')
def config_detail(config_id):
    """جزئیات کانفیگ"""
    config = Config.query.get_or_404(config_id)
    return render_template('config_detail.html', config=config)


@app.route('/order/<int:config_id>', methods=['POST'])
@login_required
def create_order(config_id):
    """ایجاد سفارش"""
    config = Config.query.get_or_404(config_id)

    if config.stock <= 0:
        flash('موجودی تمام شده است!', 'danger')
        return redirect(url_for('config_detail', config_id=config_id))

    # Create order
    order = Order(
        user_id=current_user.id,
        config_id=config_id,
        amount=config.price,
        status='pending'
    )
    db.session.add(order)
    db.session.commit()

    # Redirect to payment page
    flash(f'سفارش شما با شماره #{order.id} ثبت شد.', 'success')
    return redirect(url_for('payment.payment_page', order_id=order.id))


@app.route('/orders')
@login_required
def my_orders():
    """سفارشات من"""
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)


@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """جزئیات سفارش"""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return render_template('order_detail.html', order=order)


# ==================== Admin Routes ====================

@app.route('/admin')
@admin_required
def admin_dashboard():
    """پنل مدیریت"""
    total_users = User.query.count()
    total_configs = Config.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.amount)).filter(
        Order.status.in_(['paid', 'completed'])
    ).scalar() or 0

    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_configs=total_configs,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         recent_orders=recent_orders)


@app.route('/admin/configs')
@admin_required
def admin_configs():
    """مدیریت کانفیگ‌ها"""
    configs = Config.query.order_by(Config.created_at.desc()).all()
    return render_template('admin/configs.html', configs=configs)


@app.route('/admin/config/new', methods=['GET', 'POST'])
@admin_required
def admin_config_new():
    """افزودن کانفیگ جدید"""
    if request.method == 'POST':
        config = Config(
            name=request.form['name'],
            description=request.form.get('description', ''),
            config_data=request.form['config_data'],
            price=int(request.form['price']),
            duration_days=int(request.form.get('duration_days', 30)),
            server_location=request.form.get('server_location', ''),
            stock=int(request.form.get('stock', 0)),
            is_active='is_active' in request.form
        )
        db.session.add(config)
        db.session.commit()
        flash('کانفیگ با موفقیت اضافه شد!', 'success')
        return redirect(url_for('admin_configs'))

    return render_template('admin/config_form.html', config=None)


@app.route('/admin/config/<int:config_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_config_edit(config_id):
    """ویرایش کانفیگ"""
    config = Config.query.get_or_404(config_id)

    if request.method == 'POST':
        config.name = request.form['name']
        config.description = request.form.get('description', '')
        config.config_data = request.form['config_data']
        config.price = int(request.form['price'])
        config.duration_days = int(request.form.get('duration_days', 30))
        config.server_location = request.form.get('server_location', '')
        config.stock = int(request.form.get('stock', 0))
        config.is_active = 'is_active' in request.form
        db.session.commit()
        flash('کانفیگ با موفقیت ویرایش شد!', 'success')
        return redirect(url_for('admin_configs'))

    return render_template('admin/config_form.html', config=config)


@app.route('/admin/config/<int:config_id>/delete', methods=['POST'])
@admin_required
def admin_config_delete(config_id):
    """حذف کانفیگ"""
    config = Config.query.get_or_404(config_id)
    db.session.delete(config)
    db.session.commit()
    flash('کانفیگ حذف شد!', 'success')
    return redirect(url_for('admin_configs'))


@app.route('/admin/payment-settings', methods=['GET', 'POST'])
@admin_required
def admin_payment_settings():
    """تنظیمات پرداخت کارت به کارت"""
    if request.method == 'POST':
        SiteSettings.set('card_number', request.form.get('card_number', ''))
        SiteSettings.set('bank_name', request.form.get('bank_name', ''))
        SiteSettings.set('shaba', request.form.get('shaba', ''))
        SiteSettings.set('card_holder', request.form.get('card_holder', ''))
        flash('تنظیمات پرداخت ذخیره شد!', 'success')
        return redirect(url_for('admin_payment_settings'))

    return render_template('admin/payment_settings.html',
                         card_number=SiteSettings.get('card_number', ''),
                         bank_name=SiteSettings.get('bank_name', ''),
                         shaba=SiteSettings.get('shaba', ''),
                         card_holder=SiteSettings.get('card_holder', ''))


@app.route('/admin/users')
@admin_required
def admin_users():
    """مدیریت کاربران"""
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/admin/user/<int:user_id>/toggle', methods=['POST'])
@admin_required
def admin_user_toggle(user_id):
    """فعال/غیرفعال کردن کاربر"""
    user = User.query.get_or_404(user_id)
    user.is_active_user = not user.is_active_user
    db.session.commit()
    status = 'فعال' if user.is_active_user else 'غیرفعال'
    flash(f'کاربر {user.username} {status} شد!', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/orders')
@admin_required
def admin_orders():
    """مدیریت سفارشات"""
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)


@app.route('/admin/order/<int:order_id>/status', methods=['POST'])
@admin_required
def admin_order_status(order_id):
    """تغییر وضعیت سفارش"""
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status in ['pending', 'paid', 'completed', 'cancelled']:
        order.status = new_status
        if new_status == 'paid':
            order.paid_at = datetime.utcnow()
        db.session.commit()
        flash('وضعیت سفارش تغییر کرد!', 'success')
    return redirect(url_for('admin_orders'))


@app.route('/admin/github-sync', methods=['POST'])
@admin_required
def admin_github_sync():
    """همگام‌سازی با GitHub"""
    try:
        import requests as req
        headers = {'Authorization': f'token {GITHUB_TOKEN}'}
        url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_CONFIGS_PATH}'

        response = req.get(url, headers=headers)
        if response.status_code == 200:
            files = response.json()
            synced = 0
            for file in files:
                if file['name'].endswith('.json'):
                    content_response = req.get(file['download_url'])
                    if content_response.status_code == 200:
                        config_data = content_response.json()
                        existing = Config.query.filter_by(github_path=file['path']).first()
                        if not existing:
                            new_config = Config(
                                name=config_data.get('name', file['name']),
                                description=config_data.get('description', ''),
                                config_data=json.dumps(config_data.get('config', {})),
                                price=config_data.get('price', 0),
                                duration_days=config_data.get('duration_days', 30),
                                server_location=config_data.get('server_location', ''),
                                stock=config_data.get('stock', 0),
                                github_path=file['path'],
                                is_active=True
                            )
                            db.session.add(new_config)
                            synced += 1
            db.session.commit()
            flash(f'{synced} کانفیگ از GitHub همگام‌سازی شد!', 'success')
        else:
            flash('خطا در اتصال به GitHub!', 'danger')
    except Exception as e:
        flash(f'خطا: {str(e)}', 'danger')

    return redirect(url_for('admin_configs'))


# ==================== Auth Routes ====================

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    """ورود"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password) and user.is_active_user:
            login_user(user, remember=True)
            flash('خوش آمدید!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است!', 'danger')

    return render_template('auth/login.html')


@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    """ثبت‌نام"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('رمز عبور مطابقت ندارد!', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('این نام کاربری قبلا استفاده شده!', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('این ایمیل قبلا ثبت شده!', 'danger')
            return render_template('auth/register.html')

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('ثبت‌نام با موفقیت انجام شد!现在اکنون می‌توانید وارد شوید.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/auth/logout')
@login_required
def logout():
    """خروج"""
    logout_user()
    flash('شما خارج شدید.', 'info')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    """پروفایل کاربر"""
    return render_template('profile.html')


# ==================== API Endpoints ====================

@app.route('/api/configs')
def api_configs():
    """لیست کانفیگ‌ها"""
    configs = Config.query.filter_by(is_active=True).all()
    return jsonify([c.to_dict() for c in configs])


@app.route('/api/config/<int:config_id>')
def api_config(config_id):
    """جزئیات کانفیگ"""
    config = Config.query.get_or_404(config_id)
    return jsonify(config.to_dict())


@app.route('/api/order/<int:order_id>')
@login_required
def api_order(order_id):
    """جزئیات سفارش"""
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    return jsonify(order.to_dict())


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500


# ==================== CLI Commands ====================

@app.cli.command('init-db')
def init_db():
    """ایجاد دیتابیس و ادمین پیش‌فرض"""
    db.create_all()

    admin_username = os.getenv('ADMIN_USERNAME', 'admin')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

    if not User.query.filter_by(username=admin_username).first():
        admin = User(
            username=admin_username,
            email='admin@example.com',
            is_admin=True
        )
        admin.set_password(admin_password)
        db.session.add(admin)
        db.session.commit()
        print(f'Admin user "{admin_username}" created!')
    else:
        print('Admin user already exists!')

    print('Database initialized!')


@app.cli.command('create-sample-data')
def create_sample_data():
    """ایجاد داده‌های نمونه"""
    sample_configs = [
        {
            'name': 'کانفیگ VIP آمریکا',
            'description': 'سرور پرسرعت آمریکا مناسب برای استفاده روزانه',
            'config_data': json.dumps({"inbounds": [{"port": 1080, "protocol": "socks"}], "outbounds": [{"protocol": "vmess", "settings": {"vnext": [{"address": "us1.example.com", "port": 443}]}}]}),
            'price': 50000,
            'duration_days': 30,
            'server_location': 'آمریکا',
            'stock': 10
        },
        {
            'name': 'کانفیگ استاندارد آلمان',
            'description': 'سرور پایدار آلمان',
            'config_data': json.dumps({"inbounds": [{"port": 1080, "protocol": "socks"}], "outbounds": [{"protocol": "vmess", "settings": {"vnext": [{"address": "de1.example.com", "port": 443}]}}]}),
            'price': 35000,
            'duration_days': 30,
            'server_location': 'آلمان',
            'stock': 20
        },
        {
            'name': 'کانفیگ ویژه هلند',
            'description': 'سرور اختصاصی هلند با پورت اختصاصی',
            'config_data': json.dumps({"inbounds": [{"port": 1080, "protocol": "socks"}], "outbounds": [{"protocol": "vmess", "settings": {"vnext": [{"address": "nl1.example.com", "port": 443}]}}]}),
            'price': 45000,
            'duration_days': 30,
            'server_location': 'هلند',
            'stock': 15
        }
    ]

    for config_data in sample_configs:
        config = Config(**config_data)
        db.session.add(config)

    db.session.commit()
    print('Sample data created!')


# ==================== Main ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
