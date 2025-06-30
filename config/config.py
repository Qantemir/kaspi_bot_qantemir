import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv('BOT_TOKEN')
_admin_id = os.getenv('ADMIN_ID')
ADMIN_ID = int(_admin_id) if _admin_id and _admin_id.isdigit() else None
MONGO_URI = os.getenv('MONGO_URI')
KASPI_API = os.getenv('KASPI_API')

# Интервал проверки заказов (в секундах)
ORDER_CHECK_INTERVAL = 3600  # Интервал проверки заказов в секундах (например, 3600 = 1 час)
PRICE_CHECK_INTERVAL = 'hourly'
NOTIFY_IF_NOT_TOP1 = False
ORDER_LOOKBACK_DAYS = 4  # Количество дней, за которые ищутся заказы

ORDER_NOTIFY_ENABLED = True
