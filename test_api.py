#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к Kaspi API
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.kaspi_api import test_api_connection, get_active_orders
from config.config import KASPI_API
from loguru import logger

async def main():
    logger.info("=== Тестирование Kaspi API ===")
    
    # Проверяем наличие API ключа
    if not KASPI_API:
        logger.error("❌ KASPI_API не найден в конфигурации!")
        logger.info("Добавьте KASPI_API в файл .env")
        return
    
    logger.info(f"API ключ найден: {KASPI_API[:10]}..." if len(KASPI_API) > 10 else "API ключ найден")
    
    # Тестируем подключение
    logger.info("\n1. Тестирование подключения к API...")
    connection_ok = await test_api_connection()
    
    if not connection_ok:
        logger.error("❌ Подключение к API не удалось!")
        return
    
    # Тестируем получение заказов
    logger.info("\n2. Тестирование получения заказов...")
    orders = await get_active_orders()
    
    if orders:
        logger.info(f"✅ Найдено {len(orders)} активных заказов:")
        for order in orders:
            logger.info(f"  - Заказ {order['code']}: {order['status']} / {order['state']}")
    else:
        logger.info("ℹ️ Активных заказов не найдено (это нормально, если заказов нет)")
    
    logger.info("\n=== Тестирование завершено ===")

if __name__ == "__main__":
    asyncio.run(main()) 