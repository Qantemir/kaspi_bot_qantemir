import os
import httpx
from config.config import KASPI_API
from loguru import logger
from datetime import datetime, timedelta

# Правильный URL согласно документации
KASPI_API_URL = 'https://kaspi.kz/shop/api/v2/'

headers = {
    'Content-Type': 'application/vnd.api+json',
    'X-Auth-Token': KASPI_API,
    'Accept': 'application/vnd.api+json',
    'User-Agent': 'KaspiBot/1.0',
}

async def get_orders(page=0, size=20, state=None, status=None, date_from=None, date_to=None, delivery_type=None):
    """
    Получение заказов согласно официальной документации Kaspi API
    """
    url = KASPI_API_URL + 'orders'
    
    # По умолчанию получаем заказы за последние 3 дня (max для Kaspi API)
    if not date_from:
        date_from_dt = datetime.now() - timedelta(days=3)
    else:
        date_from_dt = datetime.strptime(date_from, '%Y-%m-%d')
    date_from_ms = int(date_from_dt.timestamp() * 1000)
    
    params = {
        'page[number]': page,
        'page[size]': size,
        'filter[orders][creationDate][$ge]': date_from_ms,  # Обязательный фильтр
    }
    
    # Добавляем дополнительные фильтры
    if state:
        params['filter[orders][state]'] = state
    if status:
        params['filter[orders][status]'] = status
    if delivery_type:
        params['filter[orders][deliveryType]'] = delivery_type
    if date_to:
        # Если передан date_to, преобразуем в миллисекунды
        date_to_dt = datetime.strptime(date_to, '%Y-%m-%d')
        date_to_ms = int(date_to_dt.timestamp() * 1000)
        params['filter[orders][creationDate][$le]'] = date_to_ms
    
    logger.info(f'Запрос заказов через Kaspi API: {url}')
    logger.info(f'Параметры запроса: {params}')
    logger.info(f'Заголовки: {dict(headers)}')
    
    # Проверяем, что API ключ настроен
    if not KASPI_API:
        logger.error('KASPI_API не настроен! Добавьте KASPI_API в файл .env')
        return []
    
    # Увеличиваем таймаут до 30 секунд
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            logger.info(f'Получен ответ от API: статус {resp.status_code}')
            
            if resp.status_code == 401:
                logger.error('Ошибка авторизации: неверный API ключ')
                return []
            elif resp.status_code == 403:
                logger.error('Ошибка доступа: недостаточно прав для API')
                return []
            elif resp.status_code == 404:
                logger.error('API endpoint не найден')
                return []
            
            resp.raise_for_status()
            logger.info('Успешно получены заказы через API')
            
            # Парсим ответ согласно структуре документации
            data = resp.json()
            logger.info(f'Структура ответа: {list(data.keys()) if isinstance(data, dict) else "не dict"}')
            
            orders = []
            
            if 'data' in data:
                for order_data in data['data']:
                    attributes = order_data.get('attributes', {})
                    
                    # Получаем информацию о товарах из entries
                    entries = attributes.get('entries', [])
                    products_info = []
                    if entries:
                        for entry in entries:
                            product_name = entry.get('product', {}).get('name', 'Товар')
                            quantity = entry.get('quantity', 1)
                            price = entry.get('price', 0)
                            products_info.append({
                                'name': product_name,
                                'quantity': quantity,
                                'price': price
                            })
                    
                    # Формируем полную информацию о заказе
                    order = {
                        'order_id': order_data.get('id'),
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
                        'entries': entries
                    }
                    orders.append(order)
                    logger.info(f'Обработан заказ: {order["code"]} - {order["status"]} - {order["state"]}')
            else:
                logger.warning('В ответе API нет поля "data"')
                logger.info(f'Полный ответ API: {data}')
            
            return orders
            
        except httpx.TimeoutException:
            logger.error('Таймаут при запросе к Kaspi API (30 секунд)')
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f'HTTP ошибка при запросе к Kaspi API: {e.response.status_code}')
            logger.error(f'Текст ответа: {e.response.text}')
            return []
        except Exception as e:
            logger.error(f'Ошибка при получении заказов через API: {e}')
            logger.error(f'Тип ошибки: {type(e).__name__}')
            return []

async def get_active_orders():
    """
    Получение активных заказов (новых, одобренных банком, принятых и готовых к доставке)
    """
    logger.info('Начинаем получение активных заказов...')
    
    # Получаем новые заказы по состоянию NEW
    logger.info('Запрашиваем заказы с состоянием NEW...')
    new_orders = await get_orders(
        state='NEW'
    )
    
    # Получаем заказы, одобренные банком (продавец должен их принять)
    logger.info('Запрашиваем заказы со статусом APPROVED_BY_BANK...')
    approved_orders = await get_orders(
        status='APPROVED_BY_BANK'
    )
    
    # Получаем заказы на самовывоз (ваша доставка)
    logger.info('Запрашиваем заказы на самовывоз (PICKUP)...')
    pickup_orders = await get_orders(
        status='ACCEPTED_BY_MERCHANT',
        delivery_type='PICKUP'
    )
    
    # Получаем заказы со статусом ACCEPTED_BY_MERCHANT и состоянием DELIVERY
    logger.info('Запрашиваем заказы со статусом ACCEPTED_BY_MERCHANT и состоянием DELIVERY...')
    delivery_orders = await get_orders(
        status='ACCEPTED_BY_MERCHANT',
        state='DELIVERY'
    )
    
    # Также получаем заказы с Kaspi Доставкой
    logger.info('Запрашиваем заказы со статусом ACCEPTED_BY_MERCHANT и состоянием KASPI_DELIVERY...')
    kaspi_orders = await get_orders(
        status='ACCEPTED_BY_MERCHANT', 
        state='KASPI_DELIVERY'
    )
    
    # Объединяем результаты
    all_orders = new_orders + approved_orders + pickup_orders + delivery_orders + kaspi_orders
    logger.info(f'Найдено {len(all_orders)} активных заказов (NEW: {len(new_orders)}, APPROVED_BY_BANK: {len(approved_orders)}, PICKUP: {len(pickup_orders)}, DELIVERY: {len(delivery_orders)}, KASPI_DELIVERY: {len(kaspi_orders)})')
    
    return all_orders

async def update_product_price(product_id: str, new_price: int):
    url = KASPI_API_URL + f'products/{product_id}/price'
    data = {"price": new_price}
    logger.info(f'Запрос обновления цены товара {product_id} через API: {new_price}')
    
    if not KASPI_API:
        logger.error('KASPI_API не настроен! Добавьте KASPI_API в файл .env')
        return {'success': False, 'error': 'no_api_key'}
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.put(url, headers=headers, json=data)
            resp.raise_for_status()
            logger.info('Цена товара успешно обновлена через API')
            return resp.json()
        except httpx.TimeoutException:
            logger.error('Таймаут при обновлении цены товара')
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            logger.error(f'Ошибка при обновлении цены товара через API: {e}')
            raise

async def create_invoice(order_id: str):
    url = KASPI_API_URL + f'orders/{order_id}/invoice'
    logger.info(f'Запрос создания накладной для заказа {order_id} через API')
    
    if not KASPI_API:
        logger.error('KASPI_API не настроен! Добавьте KASPI_API в файл .env')
        return {'success': False, 'error': 'no_api_key'}
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.post(url, headers=headers)
            resp.raise_for_status()
            logger.info('Накладная успешно создана через API')
            return resp.json()
        except httpx.TimeoutException:
            logger.error('Таймаут при создании накладной')
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            logger.error(f'Ошибка при создании накладной через API: {e}')
            raise

async def get_products():
    url = KASPI_API_URL + 'products'
    logger.info(f'Запрос списка товаров через Kaspi API: {url}')
    
    # Проверяем, что API ключ настроен
    if not KASPI_API:
        logger.error('KASPI_API не настроен! Добавьте KASPI_API в файл .env')
        return []
    
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            logger.info('Успешно получен список товаров через API')
            return resp.json()
        except httpx.TimeoutException:
            logger.error('Таймаут при запросе к Kaspi API')
            return []
        except httpx.HTTPStatusError as e:
            logger.error(f'HTTP ошибка при запросе к Kaspi API: {e.response.status_code} - {e.response.text}')
            return []
        except Exception as e:
            logger.error(f'Ошибка при получении списка товаров через API: {e}')
            return []

async def test_api_connection():
    """
    Тестирует подключение к Kaspi API
    """
    logger.info('Тестирование подключения к Kaspi API...')
    
    if not KASPI_API:
        logger.error('❌ KASPI_API не настроен! Добавьте KASPI_API в файл .env')
        return False
    
    url = KASPI_API_URL + 'orders'
    # Фильтр по дате в миллисекундах за последние 14 дней
    date_from_dt = datetime.now() - timedelta(days=14)
    date_from_ms = int(date_from_dt.timestamp() * 1000)
    params = {
        'page[number]': 0,
        'page[size]': 1,
        'filter[orders][creationDate][$ge]': date_from_ms,
    }
    logger.info(f'Тестовый запрос: {url}')
    logger.info(f'API ключ: {KASPI_API[:10]}...' if len(KASPI_API) > 10 else 'API ключ: слишком короткий')
    logger.info(f'Фильтр по дате (ms): с {date_from_ms}')
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.get(url, headers=headers, params=params)
            logger.info(f'Ответ API: статус {resp.status_code}')
            
            if resp.status_code == 200:
                logger.info('✅ Подключение к Kaspi API успешно!')
                data = resp.json()
                logger.info(f'Структура ответа: {list(data.keys()) if isinstance(data, dict) else "не dict"}')
                if 'data' in data:
                    logger.info(f'Найдено заказов: {len(data["data"])}')
                else:
                    logger.info('Заказы не найдены')
                return True
            elif resp.status_code == 401:
                logger.error('❌ Ошибка авторизации: неверный API ключ')
                return False
            elif resp.status_code == 403:
                logger.error('❌ Ошибка доступа: недостаточно прав для API')
                return False
            elif resp.status_code == 404:
                logger.error('❌ API endpoint не найден')
                return False
            else:
                logger.error(f'❌ Неожиданный статус ответа: {resp.status_code}')
                logger.error(f'Текст ответа: {resp.text}')
                return False
                
        except httpx.TimeoutException:
            logger.error('❌ Таймаут при подключении к Kaspi API')
            return False
        except Exception as e:
            logger.error(f'❌ Ошибка при тестировании API: {e}')
            return False 