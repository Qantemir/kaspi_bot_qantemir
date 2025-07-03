import os
import httpx
from config.config import KASPI_API
from loguru import logger
from datetime import datetime, timedelta

KASPI_API_URL = 'https://kaspi.kz/shop/api/v2/'

headers = {
    'Content-Type': 'application/vnd.api+json',
    'X-Auth-Token': KASPI_API,
    'Accept': 'application/vnd.api+json',
    'User-Agent': 'KaspiBot/1.0',
}


async def get_order_products(order_data: dict) -> list[dict]:
    """
    Загружает список товаров по ссылке order['relationships']['entries']['links']['related']
    """
    try:
        related_url = (
            order_data.get('relationships', {})
            .get('entries', {})
            .get('links', {})
            .get('related')
        )

        if not related_url:
            logger.warning(f"Нет ссылки на товары для заказа {order_data.get('id')}")
            return []

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(related_url, headers=headers)
            response.raise_for_status()
            data = response.json().get("data", [])

            products = []
            for item in data:
                attr = item.get("attributes", {})
                product = attr.get("product", {})
                products.append({
                    "name": product.get("name", "Товар"),
                    "quantity": attr.get("quantity", 1),
                    "price": attr.get("totalPrice", 0),
                })

            return products
    except Exception as e:
        logger.error(f"❌ Ошибка при получении товаров для заказа {order_data.get('id')}: {e}")
        return []


async def get_product_name(product_id: str):
    url = f"{KASPI_API_URL}masterproducts/{product_id}"
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data.get('data', {}).get('attributes', {}).get('name', 'Товар')
        except Exception:
            return 'Товар'

aKASPI_API_URL = 'https://kaspi.kz/shop/api/v2/'

headers = {
    'Content-Type': 'application/vnd.api+json',
    'X-Auth-Token': KASPI_API,
    'Accept': 'application/vnd.api+json',
    'User-Agent': 'KaspiBot/1.0',
}

async def get_orders(page=0, size=20, state=None, status=None, date_from=None, date_to=None, delivery_type=None):
    url = KASPI_API_URL + 'orders'

    if not date_from:
        date_from_dt = datetime.now() - timedelta(days=3)
    else:
        date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
    date_from_ms = int(date_from_dt.timestamp() * 1000)

    params = {
        'page[number]': page,
        'page[size]': size,
        'filter[orders][creationDate][$ge]': date_from_ms,
    }

    if state:
        params['filter[orders][state]'] = state
    if status:
        params['filter[orders][status]'] = status
    if delivery_type:
        params['filter[orders][deliveryType]'] = delivery_type
    if date_to:
        date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
        date_to_ms = int(date_to_dt.timestamp() * 1000)
        params['filter[orders][creationDate][$le]'] = date_to_ms

    logger.info(f'Запрос заказов через Kaspi API: {url}')
    logger.info(f'Параметры запроса: {params}')

    if not KASPI_API:
        logger.error('KASPI_API не настроен! Добавьте KASPI_API в файл .env')
        return []

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            logger.info(f'Получен ответ от API: статус {resp.status_code}')
            logger.info(f'Текст ответа от Kaspi API: {resp.text}')

            if resp.status_code in [401, 403, 404]:
                logger.error(f'Ошибка API: {resp.status_code}')
                return []

            resp.raise_for_status()
            data = resp.json()

            orders = []

            if 'data' in data:
                for order_data in data['data']:
                    attributes = order_data.get('attributes', {})
                    order_id = order_data.get('id')

                    products_info = []
                    entries_url = f"{KASPI_API_URL}orders/{order_id}/entries"
                    entries_resp = await client.get(entries_url, headers=headers)
                    entries = entries_resp.json().get("data", [])

                    for entry in entries:
                        entry_id = entry['id']
                        quantity = entry['attributes'].get('quantity', 1)
                        price = entry['attributes'].get('totalPrice', 0)

                        product_resp = await client.get(f"{KASPI_API_URL}orderentries/{entry_id}/product", headers=headers)
                        name = "Товар"
                        if product_resp.status_code == 200:
                            name = product_resp.json().get("data", {}).get("attributes", {}).get("name", "Товар")

                        products_info.append({
                            'name': name,
                            'quantity': quantity,
                            'price': price
                        })

                    order = {
                        'order_id': order_id,
                        'code': attributes.get('code'),
                        'product_name': products_info[0]['name'] if products_info else 'Товар',
                        'products': products_info,
                        'status': attributes.get('status'),
                        'state': attributes.get('state'),
                        'date': attributes.get('creationDate'),
                        'price': attributes.get('totalPrice'),
                        'customer': attributes.get('customer', {}),
                        'totalPrice': attributes.get('totalPrice'),
                        'deliveryMode': attributes.get('deliveryMode'),
                        'deliveryType': attributes.get('deliveryType'),
                        'signatureRequired': attributes.get('signatureRequired'),
                        'paymentMethod': attributes.get('paymentMethod'),
                        'paymentStatus': attributes.get('paymentStatus'),
                        'deliveryAddress': attributes.get('deliveryAddress', {}),
                        'pickupPoint': attributes.get('pickupPoint', {}),
                        'comment': attributes.get('comment', ''),
                        'waybillNumber': attributes.get('waybillNumber'),
                        'assembled': attributes.get('assembled'),
                        'courierTransmissionDate': attributes.get('kaspiDelivery', {}).get('courierTransmissionDate'),
                        'waybill': attributes.get('kaspiDelivery', {}).get('waybill'),
                    }
                    orders.append(order)
                    logger.info(f'Обработан заказ: {order["code"]} - {order["status"]} - {order["state"]}')
            else:
                logger.warning('В ответе API нет поля "data"')

            return orders

        except httpx.TimeoutException:
            logger.error('Таймаут при запросе к Kaspi API (30 секунд)')
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f'HTTP ошибка: {e.response.status_code}')
            return []
        except Exception as e:
            logger.error(f'Ошибка при получении заказов: {e}')
            return []