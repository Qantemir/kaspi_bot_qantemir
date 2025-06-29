from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from database.db import db
from database.models import PRODUCTS_COLLECTION
from config.config import ADMIN_ID
from services.order_checker import  order_check_scheduler, show_new_orders
from utils.keyboards import main_menu_kb, orders_menu_kb, prices_menu_kb, prices_interval_kb, invoices_menu_kb, settings_menu_kb, cancel_kb, confirm_kb
from loguru import logger
import asyncio
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

router = Router()

# Глобальные переменные для управления уведомлениями о заказах
order_notify_task = None
order_notify_enabled = False

# Фильтр только для админа - убираем, чтобы команда /start работала для всех
# @router.message(F.from_user.id != ADMIN_ID)
# async def block_non_admin(message: types.Message):
#     logger.warning(f'Попытка доступа не-админа: {message.from_user.id}')
#     await message.answer('⛔️ Доступ запрещён', reply_markup=main_menu_kb())

@router.message(F.text == 'Добавить товар')
async def cmd_add(message: types.Message, state: FSMContext):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    logger.info('Пользователь начал добавление товара')
    await state.set_state(AddProduct.name)
    await message.answer('✏️ Введите <b>название товара</b> для отслеживания:', reply_markup=cancel_kb)

@router.message(F.text == 'Список товаров')
async def cmd_list(message: types.Message):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    logger.info('Пользователь запросил список товаров')
    try:
        if db is None:
            await message.answer('❌ База данных недоступна. Проверьте подключение к MongoDB.', reply_markup=main_menu_kb())
            return
        products = await db[PRODUCTS_COLLECTION].find().to_list(100)
        if not products:
            logger.info('Список товаров пуст')
            await message.answer('📋 Список товаров пуст.', reply_markup=main_menu_kb())
            return
        text = '\n'.join([f"{idx+1}. <b>{p['name']}</b> — {p.get('last_price', 'нет цены')} ₸" for idx, p in enumerate(products)])
        await message.answer(f'📋 <b>Товары:</b>\n{text}', reply_markup=main_menu_kb())
    except Exception as e:
        logger.error(f'Ошибка при получении списка товаров: {e}')
        await message.answer('❌ Ошибка при получении списка товаров. Проверьте подключение к базе данных.', reply_markup=main_menu_kb())

@router.message(F.text == 'Удалить товар')
async def cmd_delete(message: types.Message, state: FSMContext):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    logger.info('Пользователь начал удаление товара')
    try:
        if db is None:
            await message.answer('❌ База данных недоступна. Проверьте подключение к MongoDB.', reply_markup=main_menu_kb())
            return
        products = await db[PRODUCTS_COLLECTION].find().to_list(100)
        if not products:
            logger.info('Список товаров пуст (удаление)')
            await message.answer('📋 Список товаров пуст.', reply_markup=main_menu_kb())
            return
        text = '\n'.join([f"{idx+1}. <b>{p['name']}</b>" for idx, p in enumerate(products)])
        await state.update_data(products=products)
        await state.set_state('await_delete_number')
        await message.answer(f'🗑️ <b>Удаление товара</b>\nВыберите номер товара для удаления:\n{text}', reply_markup=cancel_kb)
    except Exception as e:
        logger.error(f'Ошибка при получении списка товаров для удаления: {e}')
        await message.answer('❌ Ошибка при получении списка товаров. Проверьте подключение к базе данных.', reply_markup=main_menu_kb())

@router.message(F.text == 'Проверить цены')
async def cmd_check_price(message: types.Message):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    logger.info('Пользователь инициировал проверку цен')
    await message.answer('🔄 Проверяю цены... (скоро будет доступно)', reply_markup=main_menu_kb())

@router.message(F.text == 'Проверить заказы')
async def cmd_check_orders(message: types.Message, bot):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    logger.info('Пользователь инициировал проверку заказов')
    await message.answer('Ищу новые заказы...', reply_markup=main_menu_kb())
    try:
        await show_new_orders(bot)
        await message.answer('', reply_markup=main_menu_kb())
    except Exception as e:
        logger.error(f'Ошибка при проверке заказов: {e}')
        await message.answer('❌ Произошла ошибка при поиске заказов.', reply_markup=main_menu_kb())

@router.message(F.text == '❌ Отмена')
async def cancel_any(message: types.Message, state: FSMContext):
    logger.info('Пользователь отменил действие')
    await state.clear()
    await message.answer('❌ Действие отменено.', reply_markup=main_menu_kb())

@router.message(F.state == 'await_delete_number')
async def process_delete_number(message: types.Message, state: FSMContext):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    if message.text == '❌ Отмена':
        logger.info('Пользователь отменил удаление товара')
        await state.clear()
        await message.answer('❌ Удаление отменено.', reply_markup=main_menu_kb())
        return
    data = await state.get_data()
    products = data.get('products', [])
    try:
        idx = int(message.text.strip()) - 1
        assert 0 <= idx < len(products)
    except (ValueError, AssertionError):
        logger.warning('Пользователь ввёл некорректный номер товара для удаления')
        await message.answer('⚠️ Введите корректный номер!', reply_markup=cancel_kb)
        return
    product = products[idx]
    logger.info(f'Пользователь выбрал товар для удаления: {product["name"]}')
    await state.update_data(delete_idx=idx)
    await state.set_state('await_delete_confirm')
    await message.answer(f'Удалить <b>{product["name"]}</b>?', reply_markup=confirm_kb)

@router.message(F.state == 'await_delete_confirm')
async def process_delete_confirm(message: types.Message, state: FSMContext):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    if message.text == '❌ Отмена' or message.text == 'Нет':
        logger.info('Пользователь отменил подтверждение удаления товара')
        await state.clear()
        await message.answer('❌ Удаление отменено.', reply_markup=main_menu_kb())
        return
    if message.text == 'Да':
        data = await state.get_data()
        products = data.get('products', [])
        idx = data.get('delete_idx')
        if idx is not None and 0 <= idx < len(products):
            product = products[idx]
            logger.info(f'Товар удалён: {product["name"]}')
            try:
                if db is None:
                    await message.answer('❌ База данных недоступна. Проверьте подключение к MongoDB.', reply_markup=main_menu_kb())
                    await state.clear()
                    return
                await db[PRODUCTS_COLLECTION].delete_one({'_id': product['_id']})
                await message.answer(f"🗑️ Товар <b>{product['name']}</b> удалён!", reply_markup=main_menu_kb())
            except Exception as e:
                logger.error(f'Ошибка при удалении товара: {e}')
                await message.answer('❌ Ошибка при удалении товара. Проверьте подключение к базе данных.', reply_markup=main_menu_kb())
        else:
            logger.error('Ошибка удаления товара: индекс вне диапазона')
            await message.answer('⚠️ Ошибка удаления.', reply_markup=main_menu_kb())
        await state.clear()
    else:
        logger.warning('Пользователь не выбрал Да/Нет при подтверждении удаления')
        await message.answer('Пожалуйста, выберите "Да" или "Нет".', reply_markup=confirm_kb)

# Главное меню
@router.message(F.text == '⬅️ В меню')
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('📱 <b>Главное меню</b>', reply_markup=main_menu_kb())

@router.message(F.text == '📦 Заказы')
async def orders_menu(message: types.Message, state: FSMContext):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    await state.clear()
    await message.answer('📦 <b>Раздел «Заказы»</b>', reply_markup=await orders_menu_kb())

@router.message(F.text == '📉 Цены')
async def prices_menu(message: types.Message, state: FSMContext):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    await state.clear()
    await message.answer('📉 <b>Раздел «Цены»</b>', reply_markup=prices_menu_kb())

@router.message(F.text == '📄 Накладные')
async def invoices_menu(message: types.Message, state: FSMContext):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    await state.clear()
    await message.answer('📄 <b>Раздел «Накладные»</b>', reply_markup=invoices_menu_kb())

@router.message(F.text == '⚙️ Настройки')
async def settings_menu(message: types.Message, state: FSMContext):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    await state.clear()
    await message.answer('⚙️ <b>Раздел «Настройки»</b>', reply_markup=settings_menu_kb())

# Заказы
@router.message(F.text == '📬 Проверить заказы сейчас')
async def check_orders_now(message: types.Message, bot):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    await message.answer('Ищу новые заказы...', reply_markup=await orders_menu_kb())
    try:
        await show_new_orders(bot)
        await message.answer('Готово! Если появятся новые заказы, вы увидите их здесь.', reply_markup=await orders_menu_kb())
    except Exception as e:
        logger.error(f'Ошибка при проверке заказов: {e}')
        await message.answer('❌ Произошла ошибка при поиске заказов.', reply_markup=await orders_menu_kb())

@router.message(F.text.in_(['🔔 Включить уведомления каждый час', '🔕 Отключить уведомления']))
async def toggle_order_notifications(message: types.Message, bot):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    global order_notify_task, order_notify_enabled
    if not order_notify_enabled:
        # Включаем уведомления
        if order_notify_task is None or order_notify_task.done():
            order_notify_task = asyncio.create_task(order_check_scheduler(bot))
        order_notify_enabled = True
        await set_order_notify_enabled(True)
        await message.answer('🔔 Уведомления о заказах включены. Теперь бот будет проверять заказы каждый час.', reply_markup=await orders_menu_kb())
    else:
        # Отключаем уведомления
        if order_notify_task and not order_notify_task.done():
            order_notify_task.cancel()
        order_notify_enabled = False
        await set_order_notify_enabled(False)
        await message.answer('🔕 Уведомления о заказах отключены.', reply_markup=await orders_menu_kb())

# Цены
@router.message(F.text == '➕ Добавить товар на отслеживание')
async def add_product_track(message: types.Message, state: FSMContext):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    await state.set_state(AddProduct.name)
    await message.answer('Введите название товара:', reply_markup=cancel_kb)

@router.message(F.text == '📋 Список отслеживаемых товаров')
async def list_tracked_products(message: types.Message):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    try:
        if db is None:
            await message.answer('❌ База данных недоступна. Проверьте подключение к MongoDB.', reply_markup=prices_menu_kb())
            return
        products = await db[PRODUCTS_COLLECTION].find().to_list(100)
        if not products:
            await message.answer('Список отслеживаемых товаров пуст.', reply_markup=prices_menu_kb())
            return
        text = '\n'.join([f"{idx+1}. {p['name']} — {p.get('last_price', 'нет цены')} ₸" for idx, p in enumerate(products)])
        await message.answer(f'<b>Отслеживаемые товары:</b>\n{text}', reply_markup=prices_menu_kb())
    except Exception as e:
        logger.error(f'Ошибка при получении списка отслеживаемых товаров: {e}')
        await message.answer('❌ Ошибка при получении списка товаров. Проверьте подключение к базе данных.', reply_markup=prices_menu_kb())

@router.message(F.text == '⏰ Установить интервал проверки цен')
async def set_price_interval(message: types.Message):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    current = await get_price_check_interval()
    text = '⏰ Выберите интервал проверки цен:'
    if current == 'hourly':
        text += '\n(Текущий: раз в час)'
    elif current == '30min':
        text += '\n(Текущий: каждые 30 мин)'
    elif current == 'daily':
        text += '\n(Текущий: раз в день)'
    await message.answer(text, reply_markup=prices_interval_kb())

@router.message(F.text.in_(['Раз в час', 'Каждые 30 мин', 'Раз в день']))
async def price_interval_selected(message: types.Message):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    mapping = {
        'Раз в час': 'hourly',
        'Каждые 30 мин': '30min',
        'Раз в день': 'daily'
    }
    value = mapping.get(message.text, 'hourly')
    await set_price_check_interval(value)
    await message.answer(f'Интервал проверки цен установлен: {message.text}', reply_markup=prices_menu_kb())

@router.message(F.text == '🔔 Оповещать если не в топ-1')
async def toggle_top1_notify(message: types.Message):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    current = await get_notify_if_not_top1()
    new_value = not current
    await set_notify_if_not_top1(new_value)
    status = 'включены' if new_value else 'отключены'
    await message.answer(f'🔔 Оповещения о позиции в топе {status}.', reply_markup=prices_menu_kb())

@router.message(F.text == '⬅️ Назад')
async def back_to_prices_menu(message: types.Message):
    await message.answer('📉 Раздел «Цены»', reply_markup=prices_menu_kb())

# Накладные
@router.message(F.text == '🧾 Сформировать накладную')
async def create_invoice_handler(message: types.Message):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    # TODO: Реализовать формирование накладной
    await message.answer('🧾 Накладная сформирована. [Скачать PDF]', reply_markup=invoices_menu_kb())

@router.message(F.text == '⬇️ Скачать все накладные')
async def download_all_invoices(message: types.Message):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    # TODO: Реализовать скачивание архива накладных
    await message.answer('⬇️ Все накладные отправлены архивом (пример)', reply_markup=invoices_menu_kb())

# Настройки
@router.message(F.text == '⏱ Настроить интервал уведомлений о заказах')
async def set_order_notify_interval(message: types.Message):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    current = await get_order_check_interval()
    text = '⏱ Выберите интервал уведомлений о заказах:'
    if current == 'hourly':
        text += '\n(Текущий: раз в час)'
    elif current == '30min':
        text += '\n(Текущий: каждые 30 мин)'
    elif current == 'daily':
        text += '\n(Текущий: раз в день)'
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Раз в час')],
            [KeyboardButton(text='Каждые 30 мин')],
            [KeyboardButton(text='Раз в день')],
            [KeyboardButton(text='⬅️ В меню')],
        ],
        resize_keyboard=True
    )
    await message.answer(text, reply_markup=kb)

@router.message(F.text.in_(['Раз в час', 'Каждые 30 мин', 'Раз в день']) & (F.reply_to_message.text.contains('уведомлений о заказах') | F.reply_to_message.text.contains('интервал уведомлений')))
async def order_interval_selected(message: types.Message):
    # Проверяем, что пользователь - администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer('⛔️ Доступ запрещён')
        return
    mapping = {
        'Раз в час': 'hourly',
        'Каждые 30 мин': '30min',
        'Раз в день': 'daily'
    }
    value = mapping.get(message.text, '30min')
    await set_order_check_interval(value)
    await message.answer(f'Интервал уведомлений о заказах установлен: {message.text}', reply_markup=settings_menu_kb())

@router.message()
async def fallback_handler(message: types.Message):
    await message.answer('Пожалуйста, используйте кнопки для работы с ботом.', reply_markup=main_menu_kb())

# Переопределить orders_menu_kb чтобы менять текст кнопки
async def orders_menu_kb():
    enabled = await get_order_notify_enabled()
    btn_text = '🔕 Отключить уведомления' if enabled else '🔔 Включить уведомления каждый час'
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='📬 Проверить заказы сейчас')],
            [KeyboardButton(text=btn_text)],
            [KeyboardButton(text='⬅️ В меню')],
        ],
        resize_keyboard=True
    )

ORDER_NOTIFY_KEY = 'order_notify_enabled'

async def get_order_notify_enabled():
    try:
        if db is None:
            logger.warning('База данных недоступна, возвращаем False для уведомлений')
            return False
        doc = await db['settings'].find_one({'_id': ORDER_NOTIFY_KEY})
        return bool(doc and doc.get('enabled'))
    except Exception as e:
        logger.warning(f'Ошибка при получении настроек уведомлений: {e}')
        return False

async def set_order_notify_enabled(value: bool):
    try:
        if db is None:
            logger.warning('База данных недоступна, пропускаем сохранение настроек уведомлений')
            return
        await db['settings'].update_one({'_id': ORDER_NOTIFY_KEY}, {'$set': {'enabled': value}}, upsert=True)
    except Exception as e:
        logger.warning(f'Ошибка при сохранении настроек уведомлений: {e}')

async def init_order_notify_state(bot):
    global order_notify_enabled, order_notify_task
    try:
        order_notify_enabled = await get_order_notify_enabled()
        if order_notify_enabled:
            if order_notify_task is None or order_notify_task.done():
                order_notify_task = asyncio.create_task(order_check_scheduler(bot))
    except Exception as e:
        logger.warning(f'Ошибка при инициализации состояния уведомлений: {e}')
        order_notify_enabled = False

PRICE_INTERVAL_KEY = 'price_check_interval'
ORDER_INTERVAL_KEY = 'order_check_interval'
NOTIFY_TOP1_KEY = 'notify_if_not_top1'

async def get_price_check_interval():
    try:
        if db is None:
            logger.warning('База данных недоступна, возвращаем hourly для интервала цен')
            return 'hourly'
        doc = await db['settings'].find_one({'_id': PRICE_INTERVAL_KEY})
        return doc['value'] if doc and 'value' in doc else 'hourly'
    except Exception as e:
        logger.warning(f'Ошибка при получении интервала проверки цен: {e}')
        return 'hourly'

async def set_price_check_interval(value: str):
    try:
        if db is None:
            logger.warning('База данных недоступна, пропускаем сохранение интервала цен')
            return
        await db['settings'].update_one({'_id': PRICE_INTERVAL_KEY}, {'$set': {'value': value}}, upsert=True)
    except Exception as e:
        logger.warning(f'Ошибка при сохранении интервала проверки цен: {e}')

async def get_order_check_interval():
    try:
        if db is None:
            logger.warning('База данных недоступна, возвращаем 30min для интервала заказов')
            return '30min'
        doc = await db['settings'].find_one({'_id': ORDER_INTERVAL_KEY})
        return doc['value'] if doc and 'value' in doc else '30min'
    except Exception as e:
        logger.warning(f'Ошибка при получении интервала уведомлений о заказах: {e}')
        return '30min'

async def set_order_check_interval(value: str):
    try:
        if db is None:
            logger.warning('База данных недоступна, пропускаем сохранение интервала заказов')
            return
        await db['settings'].update_one({'_id': ORDER_INTERVAL_KEY}, {'$set': {'value': value}}, upsert=True)
    except Exception as e:
        logger.warning(f'Ошибка при сохранении интервала уведомлений о заказах: {e}')

async def get_notify_if_not_top1():
    try:
        if db is None:
            logger.warning('База данных недоступна, возвращаем False для уведомлений о топе')
            return False
        doc = await db['settings'].find_one({'_id': NOTIFY_TOP1_KEY})
        return bool(doc and doc.get('enabled'))
    except Exception as e:
        logger.warning(f'Ошибка при получении настроек уведомлений о топе: {e}')
        return False

async def set_notify_if_not_top1(value: bool):
    try:
        if db is None:
            logger.warning('База данных недоступна, пропускаем сохранение настроек уведомлений о топе')
            return
        await db['settings'].update_one({'_id': NOTIFY_TOP1_KEY}, {'$set': {'enabled': value}}, upsert=True)
    except Exception as e:
        logger.warning(f'Ошибка при сохранении настроек уведомлений о топе: {e}')

# --- Применение настроек при старте ---
async def init_all_settings(bot):
    try:
        await init_order_notify_state(bot)
        # Здесь можно добавить запуск фоновых задач с нужными интервалами, если потребуется
    except Exception as e:
        logger.warning(f'Ошибка при инициализации настроек: {e}') 