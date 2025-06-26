from aiogram.fsm.state import StatesGroup, State
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from database.db import db
from database.models import PRODUCTS_COLLECTION

class AddProduct(StatesGroup):
    name = State()
    link = State()
    min_price = State()

async def add_product_handlers(router):
    @router.message(AddProduct.name)
    async def process_name(message: types.Message, state: FSMContext):
        await state.update_data(name=message.text)
        await state.set_state(AddProduct.link)
        await message.answer('Вставьте ссылку на Kaspi:')

    @router.message(AddProduct.link)
    async def process_link(message: types.Message, state: FSMContext):
        await state.update_data(link=message.text)
        await state.set_state(AddProduct.min_price)
        await message.answer('Укажите минимальную допустимую цену (₸):')

    @router.message(AddProduct.min_price)
    async def process_min_price(message: types.Message, state: FSMContext):
        try:
            min_price = int(message.text.replace(' ', ''))
        except ValueError:
            await message.answer('Введите число!')
            return
        data = await state.get_data()
        product = {
            'name': data['name'],
            'link': data['link'],
            'min_price': min_price,
            'last_price': None,
            'last_order_date': None
        }
        await db[PRODUCTS_COLLECTION].insert_one(product)
        await message.answer(f"✅ Товар <b>{data['name']}</b> добавлен!")
        await state.clear() 