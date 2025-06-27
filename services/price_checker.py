import asyncio
from database.db import db
from database.models import PRODUCTS_COLLECTION
from services.kaspi_parser import get_kaspi_prices
from services.kaspi_api import get_products
from utils.notifications import notify_admin
from config.config import ADMIN_ID
from datetime import datetime, timedelta
from loguru import logger
import traceback

async def check_all_prices(bot):
    logger.info('Старт проверки всех цен через Kaspi API')
    try:
        api_products = await get_products()
    except Exception as e:
        logger.error(f'Ошибка получения товаров через API: тип: {type(e).__name__}, ошибка: {e}\n{traceback.format_exc()}')
        await notify_admin(bot, f'❌ Ошибка получения товаров через API: {e}')
        return
    for api_product in api_products:
        name = api_product.get('name')
        product_id = api_product.get('id')
        price = api_product.get('price')
        # Синхронизируем с БД (MongoDB)
        db_product = await db[PRODUCTS_COLLECTION].find_one({'product_id': product_id})
        if db_product:
            last_price = db_product.get('last_price')
            min_price = db_product.get('min_price')
            await db[PRODUCTS_COLLECTION].update_one({'_id': db_product['_id']}, {'$set': {'last_price': price}})
            logger.info(f'Обновлена цена в БД для {name}: {price}')
            if last_price and price != last_price:
                logger.info(f'Цена на {name} обновлена: было {last_price} → стало {price}')
                await notify_admin(bot, f'ℹ️ Цена на <b>{name}</b> обновлена: было {last_price:,} → стало {price:,} ₸'.replace(',', ' '))
        else:
            # Новый товар — добавляем в БД
            await db[PRODUCTS_COLLECTION].insert_one({
                'name': name,
                'product_id': product_id,
                'last_price': price,
                'min_price': None,
                'last_order_date': None
            })
            logger.info(f'Добавлен новый товар в БД: {name}')
    # Если нужно сравнивать с конкурентами — оставить парсинг сайта для этого

async def check_sleeping_products(bot):
    logger.info('Проверка "спящих" товаров (не продавались 10 дней)')
    ten_days_ago = datetime.utcnow() - timedelta(days=10)
    products = await db[PRODUCTS_COLLECTION].find().to_list(100)
    for product in products:
        last_order_date = product.get('last_order_date')
        if not last_order_date:
            continue
        try:
            last_dt = last_order_date if isinstance(last_order_date, datetime) else datetime.fromisoformat(last_order_date)
        except Exception as e:
            logger.error(f'Ошибка преобразования даты для {product["name"]}: {e}')
            continue
        if last_dt < ten_days_ago:
            logger.info(f'Товар {product["name"]} давно не продавался (последний заказ: {last_dt})')
            await notify_admin(bot, f'📉 Товар <b>{product["name"]}</b> давно не продаётся')

async def price_check_scheduler(bot):
    logger.info('Запуск фонового планировщика проверки цен')
    while True:
        await check_all_prices(bot)
        await check_sleeping_products(bot)
        await asyncio.sleep(1800)  # 30 минут 