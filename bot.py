import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from config.config import BOT_TOKEN, ADMIN_ID
from loguru import logger
from handlers import admin
from handlers.fsm_add_product import add_product_handlers
from services.price_checker import price_check_scheduler
from services.order_checker import order_check_scheduler

async def admin_only(handler):
    async def wrapper(message: types.Message, *args, **kwargs):
        if message.from_user.id != ADMIN_ID:
            await message.answer('⛔️ Доступ запрещён')
            return
        return await handler(message, *args, **kwargs)
    return wrapper

async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode='HTML')
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin.router)
    await add_product_handlers(admin.router)

    @dp.message(Command('start'))
    @admin_only
    async def start_cmd(message: types.Message):
        await message.answer('👋 Привет! Это приватный Kaspi-бот.')

    logger.info('Бот запущен')
    asyncio.create_task(price_check_scheduler(bot))
    asyncio.create_task(order_check_scheduler(bot))
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 