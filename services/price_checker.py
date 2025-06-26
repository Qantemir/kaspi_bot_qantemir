import asyncio
from database.db import db
from database.models import PRODUCTS_COLLECTION
from services.kaspi_parser import get_kaspi_prices
from utils.notifications import notify_admin
from config.config import ADMIN_ID
from datetime import datetime, timedelta

async def check_all_prices(bot):
    products = await db[PRODUCTS_COLLECTION].find().to_list(100)
    for product in products:
        url = product['link']
        name = product['name']
        min_price = product['min_price']
        last_price = product.get('last_price')
        try:
            price, competitors = await get_kaspi_prices(url)
        except Exception as e:
            await notify_admin(bot, f'❌ Ошибка парсинга для {name}: {e}')
            continue
        # Обновляем цену в БД
        await db[PRODUCTS_COLLECTION].update_one({'_id': product['_id']}, {'$set': {'last_price': price}})
        # Если цена изменилась
        if last_price and price != last_price:
            await notify_admin(bot, f'ℹ️ Цена на <b>{name}</b> обновлена: было {last_price:,} → стало {price:,} ₸'.replace(',', ' '))
        # Если цена выше, чем у конкурентов
        if competitors:
            min_competitor = min([c['price'] for c in competitors if c['price'] is not None], default=None)
            if min_competitor and price > min_competitor:
                await notify_admin(bot, f'⚠️ У тебя не самая низкая цена на <b>{name}</b>!')

async def check_sleeping_products(bot):
    ten_days_ago = datetime.utcnow() - timedelta(days=10)
    products = await db[PRODUCTS_COLLECTION].find().to_list(100)
    for product in products:
        last_order_date = product.get('last_order_date')
        if not last_order_date:
            continue
        try:
            last_dt = last_order_date if isinstance(last_order_date, datetime) else datetime.fromisoformat(last_order_date)
        except Exception:
            continue
        if last_dt < ten_days_ago:
            await notify_admin(bot, f'📉 Товар <b>{product["name"]}</b> давно не продаётся')

async def price_check_scheduler(bot):
    while True:
        await check_all_prices(bot)
        await check_sleeping_products(bot)
        await asyncio.sleep(1800)  # 30 минут 