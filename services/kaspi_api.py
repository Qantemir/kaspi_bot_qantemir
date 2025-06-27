import os
import httpx
from config.config import KASPI_API
from loguru import logger

KASPI_API_URL = 'https://kaspi.kz/shop/api/v2/'  # Пример, уточните актуальный endpoint

headers = {
    'Content-Type': 'application/vnd.api+json',
    'X-Auth-Token': KASPI_API,
    'Accept': 'application/vnd.api+json',
}

async def get_orders(page=0, size=20, state=None, status=None, date_from=None, date_to=None):
    url = KASPI_API_URL + 'orders'
    params = {
        'page[number]': page,
        'page[size]': size,
    }
    if state:
        params['filter[orders][state]'] = state
    if status:
        params['filter[orders][status]'] = status
    if date_from:
        params['filter[orders][creationDate][$ge]'] = date_from
    if date_to:
        params['filter[orders][creationDate][$le]'] = date_to
    logger.info(f'Запрос заказов через Kaspi API: {url} c params={params}')
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            logger.info('Успешно получены заказы через API')
            return resp.json()
        except Exception as e:
            logger.error(f'Ошибка при получении заказов через API: {e}')
            raise

async def update_product_price(product_id: str, new_price: int):
    url = KASPI_API_URL + f'products/{product_id}/price'
    data = {"price": new_price}
    logger.info(f'Запрос обновления цены товара {product_id} через API: {new_price}')
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.put(url, headers=headers, json=data)
            resp.raise_for_status()
            logger.info('Цена товара успешно обновлена через API')
            return resp.json()
        except Exception as e:
            logger.error(f'Ошибка при обновлении цены товара через API: {e}')
            raise

async def create_invoice(order_id: str):
    url = KASPI_API_URL + f'orders/{order_id}/invoice'
    logger.info(f'Запрос создания накладной для заказа {order_id} через API')
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            logger.info('Накладная успешно создана через API')
            return resp.json()
        except Exception as e:
            logger.error(f'Ошибка при создании накладной через API: {e}')
            raise

async def get_products():
    url = KASPI_API_URL + 'products'
    logger.info(f'Запрос списка товаров через Kaspi API: {url}')
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            logger.info('Успешно получен список товаров через API')
            return resp.json()
        except Exception as e:
            logger.error(f'Ошибка при получении списка товаров через API: {e}')
            raise 