import httpx
from config.config import KASPI_API
from loguru import logger

KASPI_API_URL = 'https://kaspi.kz/shop/api/v2/'

headers = {
    'Content-Type': 'application/vnd.api+json',
    'X-Auth-Token': KASPI_API,
    'Accept': 'application/vnd.api+json',
    'User-Agent': 'KaspiBot/1.0',
}

async def create_invoice(order_id: str, number_of_space: int = 1):
    """
    Формирует накладную (меняет статус заказа на ASSEMBLE) через Kaspi API
    """
    url = KASPI_API_URL + f'orders/{order_id}'
    payload = {
        "data": {
            "type": "orders",
            "id": order_id,
            "attributes": {
                "status": "ASSEMBLE",
                "numberOfSpace": str(number_of_space)
            }
        }
    }
    logger.info(f'Запрос формирования накладной для заказа {order_id} через API (numberOfSpace={number_of_space})')
    if not KASPI_API:
        logger.error('KASPI_API не настроен! Добавьте KASPI_API в файл .env')
        return {'success': False, 'error': 'no_api_key'}
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.patch(url, headers=headers, json=payload)
            resp.raise_for_status()
            logger.info('Накладная успешно сформирована через API (статус ASSEMBLE)')
            return resp.json()
        except httpx.TimeoutException:
            logger.error('Таймаут при формировании накладной')
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            logger.error(f'Ошибка при формировании накладной через API: {e}')
            return {'success': False, 'error': str(e)}

async def download_invoice_pdf(waybill_url: str, filename: str = None) -> bytes:
    """
    Скачивает PDF накладной по ссылке waybill_url и возвращает байты файла.
    """
    if not waybill_url:
        raise ValueError('Не передан URL для скачивания накладной')
    logger.info(f'Скачивание PDF накладной: {waybill_url}')
    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/pdf,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://kaspi.kz/'
    }
    async with httpx.AsyncClient(timeout=30, headers=browser_headers) as client:
        resp = await client.get(waybill_url)
        resp.raise_for_status()
        return resp.content