from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='/add'), KeyboardButton(text='/list')],
        [KeyboardButton(text='/delete'), KeyboardButton(text='/check_price')],
        [KeyboardButton(text='/check_orders')],
    ],
    resize_keyboard=True
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text='❌ Отмена')]],
    resize_keyboard=True,
    one_time_keyboard=True
)

def delete_confirm_kb(product_name):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=f'Удалить {product_name}', callback_data='confirm_delete'),
                InlineKeyboardButton(text='Отмена', callback_data='cancel_delete')
            ]
        ]
    ) 