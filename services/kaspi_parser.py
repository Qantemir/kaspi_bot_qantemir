import httpx
from selectolax.parser import HTMLParser

async def fetch_kaspi_page(url: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text

def parse_price_and_competitors(html: str) -> tuple[int, list[dict]]:
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
    return price, competitors

async def get_kaspi_prices(url: str):
    html = await fetch_kaspi_page(url)
    return parse_price_and_competitors(html) 