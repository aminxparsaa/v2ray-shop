"""
V2Ray Config Shop - Payment System
سیستم پرداخت کارت به کارت
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models import db, Order, Config, SiteSettings

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/payment/<int:order_id>')
@login_required
def payment_page(order_id):
    """صفحه پرداخت"""
    order = Order.query.get_or_404(order_id)

    # Check ownership
    if order.user_id != current_user.id:
        flash('دسترسی غیرمجاز!', 'danger')
        return redirect(url_for('index'))

    if order.status != 'pending':
        flash('این سفارش قبلاً پردازش شده است.', 'info')
        return redirect(url_for('order_detail', order_id=order_id))

    # Get card info from settings
    card_number = SiteSettings.get('card_number', '۶۰۳۷-۹۹۷۰-۰۰۰۰-۰۰۰۰')
    card_holder = SiteSettings.get('card_holder', 'نام دارنده کارت')
    bank_name = SiteSettings.get('bank_name', 'بانک')
    shaba = SiteSettings.get('shaba', '')

    return render_template('payment/payment.html',
                         order=order,
                         card_number=card_number,
                         card_holder=card_holder,
                         bank_name=bank_name,
                         shaba=shaba)


@payment_bp.route('/payment/<int:order_id>/confirm', methods=['POST'])
@login_required
def payment_confirm(order_id):
    """تأیید پرداخت توسط کاربر"""
    order = Order.query.get_or_404(order_id)

    if order.user_id != current_user.id:
        flash('دسترسی غیرمجاز!', 'danger')
        return redirect(url_for('index'))

    if order.status != 'pending':
        flash('این سفارش قبلاً پردازش شده است.', 'info')
        return redirect(url_for('order_detail', order_id=order_id))

    # Get optional tracking code
    tracking_code = request.form.get('tracking_code', '')

    # Update order status
    order.status = 'paid'
    order.paid_at = datetime.utcnow()
    order.payment_id = f'card_{tracking_code}' if tracking_code else 'card_manual'
    db.session.commit()

    # Decrease stock
    config = Config.query.get(order.config_id)
    if config and config.stock > 0:
        config.stock -= 1
        db.session.commit()

    flash('پرداخت شما ثبت شد! پس از تأیید مدیر، کانفیگ برایتان ارسال می‌شود.', 'success')
    return redirect(url_for('order_detail', order_id=order_id))


@payment_bp.route('/api/payment/card-info')
def api_card_info():
    """API دریافت اطلاعات کارت"""
    card_number = SiteSettings.get('card_number', '')
    shaba = SiteSettings.get('shaba', '')
    bank_name = SiteSettings.get('bank_name', '')

    return jsonify({
        'card_number': card_number,
        'shaba': shaba,
        'bank_name': bank_name
    })
