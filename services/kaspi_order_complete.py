import httpx
from config.config import KASPI_API
from loguru import logger

KASPI_API_URL = 'https://kaspi.kz/shop/api/v2/orders'

headers_base = {
    'Content-Type': 'application/vnd.api+json',
    'X-Auth-Token': KASPI_API,
    'Accept': 'application/vnd.api+json',
    'User-Agent': 'KaspiBot/1.0',
}

async def send_order_code(order_id: str, order_code: str) -> dict:
    """
    Первый этап: отправить код клиенту (X-Security-Code пустой)
    """
    payload = {
        "data": {
            "type": "orders",
            "id": order_id,
            "attributes": {
                "code": order_code,
                "status": "COMPLETED"
            }
        }
    }
    headers = headers_base.copy()
    headers['X-Security-Code'] = ''
    headers['X-Send-Code'] = 'true'
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(KASPI_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            logger.info(f"Код для выдачи заказа {order_id} отправлен клиенту. Ответ: {resp.text}")
            return resp.json()
    except Exception as e:
        logger.error(f"Ошибка при отправке кода для выдачи заказа {order_id}: {e}")
        return {"error": str(e)}

async def complete_order(order_id: str, order_code: str, security_code: str) -> dict:
    """
    Второй этап: подтверждение выдачи заказа с кодом клиента
    """
    payload = {
        "data": {
            "type": "orders",
            "id": order_id,
            "attributes": {
                "code": order_code,
                "status": "COMPLETED"
            }
        }
    }
    headers = headers_base.copy()
    headers['X-Security-Code'] = security_code
    headers['X-Send-Code'] = 'true'
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(KASPI_API_URL, headers=headers, json=payload)
            resp.raise_for_status()
            logger.info(f"Заказ {order_id} завершён (выдан). Ответ: {resp.text}")
            return resp.json()
    except Exception as e:
        logger.error(f"Ошибка при завершении заказа {order_id}: {e}")
        return {"error": str(e)} 