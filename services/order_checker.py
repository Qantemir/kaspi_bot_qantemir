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
                await notify_admin(
                    bot,
                    f"🚚 Новый заказ в статусе '{order['status']}': <b>{order['product_name']}</b>, №{order['order_id']}"
                )

async def order_check_scheduler(bot):
    logger.info('Запуск фонового планировщика проверки заказов')
    while True:
        await check_orders(bot)
        await asyncio.sleep(1800)  # 30 минут 