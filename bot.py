import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from config.config import BOT_TOKEN, ADMIN_ID
from loguru import logger
from handlers import admin
from services.order_checker import order_check_scheduler
from aiogram.client.default import DefaultBotProperties
from utils.keyboards import main_menu_kb

def admin_only(handler):
    async def wrapper(*args, **kwargs):
        message = None
        for arg in args:
            if isinstance(arg, types.Message):
                message = arg
                break
        if not message:
            message = kwargs.get('message')
        if message and (not message.from_user or message.from_user.id != ADMIN_ID):
            await message.answer('⛔️ Доступ запрещён')
            return
        return await handler(*args, **kwargs)
    return wrapper

async def main():
    if not BOT_TOKEN:
        raise ValueError('BOT_TOKEN не задан в config/config.py или .env')
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin.router)

    @dp.message(Command('start'))
    @admin_only
    async def start_cmd(message: types.Message, **kwargs):
        await message.answer('👋 Привет! Это приватный Kaspi-бот.', reply_markup=main_menu_kb())

    logger.info('Бот запущен')
    asyncio.create_task(order_check_scheduler(bot))
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 