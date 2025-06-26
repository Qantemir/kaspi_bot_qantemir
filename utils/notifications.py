from aiogram import Bot, types
from config.config import ADMIN_ID

async def notify_admin(bot: Bot, text: str, reply_markup: types.ReplyKeyboardMarkup = None):
    await bot.send_message(ADMIN_ID, text, reply_markup=reply_markup) 