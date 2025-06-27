from aiogram import Bot, types
from config.config import ADMIN_ID
 
async def notify_admin(bot: Bot, text: str, reply_markup: types.ReplyKeyboardMarkup = None):
    """
    Отправляет уведомление админу в дружелюбном стиле.
    Пример:
    await notify_admin(bot, '🚚 <b>Новый заказ!</b>\nТовар: <b>iPhone 15 Pro</b>\nСтатус: На доставке\n№123456789')
    """
    await bot.send_message(ADMIN_ID, text, reply_markup=reply_markup) 