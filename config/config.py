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