import asyncio
from loguru import logger
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from utils.notifications import notify_admin
from services.kaspi_api import get_orders
from config.config import ORDER_CHECK_INTERVAL, ORDER_LOOKBACK_DAYS
from config.settings import ORDER_LOOKBACK_DAYS


async def safe_notify(bot, message: str, reply_markup=None):
    """
    Безопасная отправка уведомлений администратору через Telegram
    """
    if bot:
        await notify_admin(bot, message, reply_markup=reply_markup)


def format_order_date(order_date) -> str:
    """
    Преобразует дату из timestamp или строки в читаемый формат дд.мм.гггг чч:мм
    """
    if not order_date:
        return "-"
    try:
        if isinstance(order_date, (int, float)):
            dt = datetime.fromtimestamp(order_date / 1000)
        elif isinstance(order_date, datetime):
            dt = order_date
        else:
            dt = datetime.fromisoformat(order_date)
        return dt.strftime('%d.%m.%Y %H:%M')
    except Exception:
        return str(order_date)


def format_address(address: dict) -> str:
    """
    Форматирует адрес в строку
    """
    if not address:
        return ""
    parts = []
    if address.get('city'):
        parts.append(address['city'])
    if address.get('street'):
        parts.append(address['street'])
    if address.get('house'):
        parts.append(f"д. {address['house']}")
    if address.get('apartment'):
        parts.append(f"кв. {address['apartment']}")
    return ", ".join(parts)


def format_products(products: list, fallback: str = 'Товар') -> str:
    """
    Форматирует список товаров в виде: 1. Название xКол-во = Цена
    """
    if not products:
        return fallback
    lines = []
    for i, product in enumerate(products, 1):
        name = product.get('name', '—')
        qty = product.get('quantity', 1)
        price = product.get('price', 0)
        lines.append(f"{i}. {name} x{qty} = {price:,} ₸")
    return "\n".join(lines)


def get_delivery_text(state, status) -> tuple[str, str]:
    """
    Возвращает описание и эмодзи типа доставки
    """
    if state == 'NEW':
        return '🆕 Новый заказ', '🆕'
    elif status == 'APPROVED_BY_BANK':
        return '✅ Одобрен банком (требует принятия)', '✅'
    elif state == 'DELIVERY':
        return '🚚 Ваша доставка', '🚚'
    elif state == 'KASPI_DELIVERY':
        return '📦 Kaspi Доставка', '📦'
    return '📋 Готов к выдаче', '📋'


async def show_order_notification(bot, order):
    """
    Формирует и отправляет уведомление об одном заказе администратору
    """
    order_date_str = format_order_date(order.get('date'))

    customer = order.get('customer', {})
    customer_name = f"{customer.get('firstName', '')} {customer.get('lastName', '')}".strip() or 'Клиент'
    customer_phone = customer.get('phone', '')
    customer_email = customer.get('email', '')

    products_text = format_products(order.get('products', []), order.get('product_name', 'Товар'))
    total_price = order.get('totalPrice', order.get('price', 0))
    status = order.get('status', '')
    state = order.get('state', '')
    delivery_type = order.get('deliveryType', '')
    delivery_mode = order.get('deliveryMode', '')
    address_text = format_address(order.get('deliveryAddress', {}))
    payment_method = order.get('paymentMethod', '')
    payment_status = order.get('paymentStatus', '')
    payment_text = f"{payment_method} ({payment_status})" if payment_status else payment_method
    comment_text = f"\n💬 Комментарий: {order.get('comment')}" if order.get('comment') else ""
    signature_text = "\n✍️ Требуется подпись" if order.get('signatureRequired') else ""

    delivery_text, emoji = get_delivery_text(state, status)

    message = (
        f"{emoji} <b>Новый заказ!</b>\n"
        f"№{order.get('code', order.get('order_id'))}\n\n"
        f"📦 <b>Товары:</b>\n{products_text}\n"
        f"💰 <b>Сумма:</b> {total_price:,} ₸\n\n"
        f"👤 <b>Клиент:</b> {customer_name}\n"
    )

    if customer_phone:
        message += f"📞 Телефон: {customer_phone}\n"
    if customer_email:
        message += f"📧 Email: {customer_email}\n"

    message += (
        f"\n📋 <b>Статус:</b> {status}\n"
        f"🚚 <b>Тип доставки:</b> {delivery_text}\n"
    )

    if delivery_type:
        message += f"📍 <b>Способ доставки:</b> {delivery_type}\n"
    if address_text:
        message += f"🏠 <b>Адрес:</b> {address_text}\n"

    message += (
        f"💳 <b>Оплата:</b> {payment_text}\n"
        f"📅 <b>Дата:</b> {order_date_str}"
        f"{comment_text}"
        f"{signature_text}"
    )

    # Формируем кнопку в зависимости от состояния
    assembled = order.get('assembled')
    courier_transmission = order.get('courierTransmissionDate')

    if assembled is False and courier_transmission is None:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text='Сформировать накладную', callback_data=f'create_invoice:{order.get("order_id") or order.get("code")}')
        ]])
        await safe_notify(bot, message, reply_markup=kb)
    elif assembled is True and courier_transmission is None:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text='Скачать накладную', callback_data=f'download_invoice:{order.get("order_id") or order.get("code")}')
        ]])
        await safe_notify(bot, message, reply_markup=kb)
    else:
        await safe_notify(bot, message)


async def show_new_orders(bot, date_from=None):
    """
    Запрашивает новые заказы со state='KASPI_DELIVERY' и отправляет уведомления
    """
    logger.info('Запрос заказов (state=SIGN_REQUIRED)')
    if date_from is None:
        date_from = (datetime.now() + timedelta(days=1) - timedelta(days=ORDER_LOOKBACK_DAYS)).strftime('%Y-%m-%d')

    try:
        new_orders = await get_orders(state='KASPI_DELIVERY', date_from=date_from)

        if not new_orders:
            await safe_notify(bot, "📭 <b>Новых заказов не найдено</b>")
            return

        for order in new_orders:
            if order.get('assembled') is not False or order.get('courierTransmissionDate') is not None:
                continue  # Пропускаем, если уже собран или передан
            await show_order_notification(bot, order)

    except Exception as e:
        await safe_notify(bot, f"❌ Ошибка при получении заказов: {e}")


async def order_check_scheduler(bot):
    """
    Планировщик регулярной проверки новых заказов
    """
    while True:
        try:
            await show_new_orders(bot)
        except Exception as e:
            await safe_notify(bot, f"❌ Ошибка в планировщике: {e}")
        await asyncio.sleep(ORDER_CHECK_INTERVAL)
