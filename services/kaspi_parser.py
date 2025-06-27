import httpx
from selectolax.parser import HTMLParser
from loguru import logger
import traceback
import asyncio

async def fetch_kaspi_page(url: str, retries: int = 3, delay: int = 5) -> str:
    logger.info(f'Загрузка страницы Kaspi: {url}')
    for attempt in range(1, retries + 1):
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                logger.info(f'Страница успешно загружена: {url}')
                return resp.text
            except Exception as e:
                logger.error(f'Попытка {attempt}: Ошибка загрузки страницы Kaspi: {url}, тип: {type(e).__name__}, ошибка: {e}\n{traceback.format_exc()}')
                if attempt < retries:
                    await asyncio.sleep(delay)
                else:
                    raise

def parse_price_and_competitors(html: str) -> tuple[int, list[dict]]:
    logger.info('Парсинг HTML для получения цены и конкурентов')
    tree = HTMLParser(html)
    # Пример: ищем цену товара
    price_node = tree.css_first('[data-test="product-price"]')
    price = int(price_node.text().replace('₸', '').replace(' ', '')) if price_node else None
    # Пример: ищем конкурентов (может отличаться, зависит от верстки Kaspi)
    competitors = []
    for node in tree.css('div.seller-item'):
        seller = node.css_first('.seller-name')
        seller_name = seller.text(strip=True) if seller else ''
        price_node = node.css_first('.price')
        comp_price = int(price_node.text().replace('₸', '').replace(' ', '')) if price_node else None
        competitors.append({'seller': seller_name, 'price': comp_price})
    logger.info(f'Результат парсинга: price={price}, competitors={competitors}')
    return price, competitors

async def get_kaspi_prices(url: str):
    logger.info(f'Получение цен и конкурентов для: {url}')
    html = await fetch_kaspi_page(url)
    return parse_price_and_competitors(html) 