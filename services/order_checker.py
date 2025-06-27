import asyncio
from database.db import db
from database.models import ORDERS_COLLECTION, PRODUCTS_COLLECTION
from utils.notifications import notify_admin
from loguru import logger
from services.kaspi_api import get_orders

# TODO: Реализовать реальный парсер или интеграцию с API Kaspi
async def fetch_kaspi_orders():
    logger.info('Запрос заказов с Kaspi через API')
    try:
        orders = await get_orders()
        return orders
    except Exception as e:
        logger.error(f'Ошибка получения заказов через API: тип: {type(e).__name__}, ошибка: {e}')
        await notify_admin(
            bot=None,  # bot должен быть передан в вызывающей функции
            text=f'❌ <b>Ошибка получения заказов через API:</b>\n<code>{e}</code>'
        )
        return []

async def check_orders(bot):
    logger.info('Старт проверки заказов')
    new_orders = await fetch_kaspi_orders()
    for order in new_orders:
        exists = await db[ORDERS_COLLECTION].find_one({'order_id': order['order_id']})
        if not exists:
            logger.info(f'Новый заказ: {order}')
            await db[ORDERS_COLLECTION].insert_one(order)
            await db[PRODUCTS_COLLECTION].update_one(
                {'name': order['product_name']},
                {'$set': {'last_order_date': order['date']}}
            )
            logger.info(f'Обновлен last_order_date для {order["product_name"]}')
            if order['status'] in ['На доставке', 'На упаковке']:
                logger.info(f'Уведомление о новом заказе: {order}')
                # Форматируем дату заказа
                order_date = order.get('date', '')
                if order_date:
                    from datetime import datetime
                    try:
                        dt = order_date if isinstance(order_date, datetime) else datetime.fromisoformat(order_date)
                        order_date_str = dt.strftime('%d.%m.%Y %H:%M')
                    except Exception:
                        order_date_str = str(order_date)
                else:
                    order_date_str = '-'
                await notify_admin(
                    bot,
                    f"🚚 <b>Новый заказ!</b>\nТовар: <b>{order['product_name']}</b>\nСтатус: <b>{order['status']}</b>\n№{order['order_id']}\nДата: {order_date_str}"
                )

async def order_check_scheduler(bot):
    logger.info('Запуск фонового планировщика проверки заказов')
    while True:
        await check_orders(bot)
        await asyncio.sleep(1800)  # 30 минут 