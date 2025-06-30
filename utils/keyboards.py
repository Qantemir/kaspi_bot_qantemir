from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📦 Заказы'), KeyboardButton(text='📉 Отслеживание цен')],
            [KeyboardButton(text='⚙️ Настройки')],
        ],
        resize_keyboard=True
    )

def orders_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📬 Проверить заказы сейчас')],
            [KeyboardButton(text='🔔 Включить уведомления каждый час')],
            [KeyboardButton(text='⬅️ В меню')],
        ],
        resize_keyboard=True
    )

def prices_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='➕ Добавить товар на отслеживание')],
            [KeyboardButton(text='📋 Список отслеживаемых товаров')],
            [KeyboardButton(text='⏰ Установить интервал проверки цен')],
            [KeyboardButton(text='🔔 Оповещать если не в топ-1')],
            [KeyboardButton(text='⬅️ В меню')],
        ],
        resize_keyboard=True
    )

def prices_interval_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Раз в час')],
            [KeyboardButton(text='Каждые 30 мин')],
            [KeyboardButton(text='Раз в день')],
            [KeyboardButton(text='⬅️ Назад')],
        ],
        resize_keyboard=True
    )

def invoices_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='🧾 Сформировать накладную')],
            [KeyboardButton(text='⬇️ Скачать все накладные')],
            [KeyboardButton(text='⬅️ В меню')],
        ],
        resize_keyboard=True
    )

def settings_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='⏱ Настроить интервал уведомлений о заказах')],
            [KeyboardButton(text='⬅️ В меню')],
        ],
        resize_keyboard=True
    )

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='❌ Отмена')]],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Для отмены нажмите кнопку'
)

confirm_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='Да'), KeyboardButton(text='Нет')]],
    resize_keyboard=True,
    one_time_keyboard=True,
    input_field_placeholder='Подтвердите действие'
) 