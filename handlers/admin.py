from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from handlers.fsm_add_product import AddProduct
from database.db import db
from database.models import PRODUCTS_COLLECTION
from config.config import ADMIN_ID
from services.order_checker import check_orders

router = Router()

# Фильтр только для админа
@router.message(F.from_user.id != ADMIN_ID)
async def block_non_admin(message: types.Message):
    await message.answer('⛔️ Доступ запрещён')

@router.message(Command('add'))
async def cmd_add(message: types.Message, state: FSMContext):
    await state.set_state(AddProduct.name)
    await message.answer('Введите название товара:')

@router.message(Command('list'))
async def cmd_list(message: types.Message):
    products = await db[PRODUCTS_COLLECTION].find().to_list(100)
    if not products:
        await message.answer('Список товаров пуст.')
        return
    text = '\n'.join([f"{idx+1}. {p['name']} — {p.get('last_price', 'нет цены')} ₸" for idx, p in enumerate(products)])
    await message.answer(f'<b>Товары:</b>\n{text}')

@router.message(Command('delete'))
async def cmd_delete(message: types.Message, state: FSMContext):
    products = await db[PRODUCTS_COLLECTION].find().to_list(100)
    if not products:
        await message.answer('Список товаров пуст.')
        return
    text = '\n'.join([f"{idx+1}. {p['name']}" for idx, p in enumerate(products)])
    await state.update_data(products=products)
    await state.set_state('await_delete_number')
    await message.answer(f'Выберите номер товара для удаления:\n{text}')

@router.message(F.state == 'await_delete_number')
async def process_delete_number(message: types.Message, state: FSMContext):
    data = await state.get_data()
    products = data.get('products', [])
    try:
        idx = int(message.text.strip()) - 1
        assert 0 <= idx < len(products)
    except (ValueError, AssertionError):
        await message.answer('Введите корректный номер!')
        return
    product = products[idx]
    await db[PRODUCTS_COLLECTION].delete_one({'_id': product['_id']})
    await message.answer(f"🗑️ Товар <b>{product['name']}</b> удалён!")
    await state.clear()

@router.message(Command('check_price'))
async def cmd_check_price(message: types.Message):
    await message.answer('🔄 Проверяю цены... (реализуем позже)')

@router.message(Command('check_orders'))
async def cmd_check_orders(message: types.Message, bot):
    await message.answer('🔄 Проверяю заказы...')
    await check_orders(bot)
    await message.answer('✅ Проверка заказов завершена.') 