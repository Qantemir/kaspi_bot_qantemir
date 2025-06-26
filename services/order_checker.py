import asyncio
from database.db import db
from database.models import ORDERS_COLLECTION, PRODUCTS_COLLECTION
from utils.notifications import notify_admin

# TODO: Реализовать реальный парсер или интеграцию с API Kaspi
async def fetch_kaspi_orders():
    # Пример: возвращаем список заказов
    # [{order_id, status, date, product_name}]
    return []

async def check_orders(bot):
    new_orders = await fetch_kaspi_orders()
    for order in new_orders:
        exists = await db[ORDERS_COLLECTION].find_one({'order_id': order['order_id']})
        if not exists:
            await db[ORDERS_COLLECTION].insert_one(order)
            # Обновляем last_order_date у товара
            await db[PRODUCTS_COLLECTION].update_one(
                {'name': order['product_name']},
                {'$set': {'last_order_date': order['date']}}
            )
            if order['status'] in ['На доставке', 'На упаковке']:
                await notify_admin(
                    bot,
                    f"🚚 Новый заказ в статусе '{order['status']}': <b>{order['product_name']}</b>, №{order['order_id']}"
                )

async def order_check_scheduler(bot):
    while True:
        await check_orders(bot)
        await asyncio.sleep(1800)  # 30 минут 