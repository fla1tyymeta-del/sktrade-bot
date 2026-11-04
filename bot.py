import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
import config
from database import Database

# Initialize database
db = Database()

# Initialize bot and dispatcher
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# States
class AddKeysState(StatesGroup):
    choosing_category = State()
    receiving_keys = State()

class DeleteKeysState(StatesGroup):
    choosing_category = State()
    viewing_keys = State()
    deleting_key = State()
    searching_key = State()

class PurchaseState(StatesGroup):
    choosing_category = State()
    awaiting_payment = State()

# Keyboards
def get_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 Купить ключ", callback_data="buy_key"),
            InlineKeyboardButton(text="📦 Наличие товара", callback_data="check_stock")
        ],
        [
            InlineKeyboardButton(text="👤 Мой профиль", callback_data="my_profile"),
            InlineKeyboardButton(text="📥 Скачать SKTrade", callback_data="download")
        ],
        [
            InlineKeyboardButton(text="💬 Поддержка", callback_data="support")
        ]
    ])
    return keyboard

def get_admin_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить ключи", callback_data="admin_add_keys"),
            InlineKeyboardButton(text="➖ Удалить ключи", callback_data="admin_delete_keys")
        ],
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")
        ]
    ])
    return keyboard

def get_categories_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    buttons = []
    for cat_id, cat_info in config.CATEGORIES.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{cat_info['name']} — {cat_info['price']}₽",
                callback_data=f"category_{cat_id}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")])
    keyboard.inline_keyboard = buttons
    return keyboard

# Handlers
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    db.add_user(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    text = (
        "👋 Добро пожаловать в магазин ключей SKTrade!\n\n"
        "Здесь вы можете купить ключи для программы SKTrade "
        "на различные сроки использования.\n\n"
        "Выберите действие в меню ниже:"
    )
    await message.answer(text, reply_markup=get_main_keyboard())

@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    user_id = message.from_user.id
    if user_id != config.ADMIN_ID:
        await message.answer("⛔ У вас нет доступа к админ-панели")
        return

    stats = db.get_admin_stats()
    text = (
        "🔐 Панель администратора\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"💰 Продаж: {stats['total_purchases']}\n"
        f"💵 Выручка: {stats['total_revenue']:.2f}₽\n\n"
        "Выберите действие:"
    )
    await message.answer(text, reply_markup=get_admin_keyboard())

@dp.callback_query(lambda c: c.data == "main_menu")
async def main_menu_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 Главное меню\n\nВыберите действие:",
        reply_markup=get_main_keyboard()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "check_stock")
async def check_stock_callback(callback: types.CallbackQuery):
    counts = db.get_all_categories_count()
    text = "📦 Наличие товара:\n\n"
    for cat_id, count in counts.items():
        cat_name = config.CATEGORIES[cat_id]["name"]
        if count > 0:
            text += f"✅ {cat_name} — {count} шт.\n"
        else:
            text += f"❌ {cat_name} — нет в наличии\n"

    text += "\n💰 Цены:"
    for cat_id, cat_info in config.CATEGORIES.items():
        text += f"\n• {cat_info['name']}: {cat_info['price']}₽"

    await callback.message.edit_text(text, reply_markup=get_main_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "download")
async def download_callback(callback: types.CallbackQuery):
    text = (
        "📥 Скачать SKTrade\n\n"
        f"Ссылка на скачивание: {config.SKTRADE_DOWNLOAD_LINK}\n\n"
        "После покупки ключа активируйте его в программе."
    )
    await callback.message.edit_text(text, reply_markup=get_main_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "support")
async def support_callback(callback: types.CallbackQuery):
    text = (
        "💬 Поддержка\n\n"
        f"Если у вас возникли проблемы, напишите: {config.SUPPORT_USERNAME}\n\n"
        "Мы ответим в ближайшее время!"
    )
    await callback.message.edit_text(text, reply_markup=get_main_keyboard())
    await callback.answer()

@dp.callback_query(lambda c: c.data == "my_profile")
async def my_profile_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    keys = db.get_user_keys(user_id)

    if not keys:
        text = "👤 Мой профиль\n\nУ вас пока нет купленных ключей."
    else:
        text = "👤 Мой профиль\n\n🔑 Ваши ключи:\n\n"
        for key in keys:
            text += f"• {key['category_name']}\n"
            text += f"  Ключ: `{key['key_value']}`\n"
            text += f"  Получен: {key['issued_at']}\n\n"

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_main_keyboard())
    await callback.answer()

# Admin handlers
@dp.callback_query(lambda c: c.data == "admin_add_keys")
async def admin_add_keys_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Нет доступа")
        return

    await state.set_state(AddKeysState.choosing_category)
    await callback.message.edit_text(
        "➕ Добавление ключей\n\nВыберите категорию:",
        reply_markup=get_categories_keyboard()
    )
    await callback.answer()

@dp.callback_query(AddKeysState.choosing_category)
async def admin_add_keys_category(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Нет доступа")
        return

    if callback.data == "main_menu":
        await state.clear()
        await callback.message.edit_text(
            "🔐 Панель администратора\n\nВыберите действие:",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    category_id = callback.data.replace("category_", "")
    await state.update_data(category_id=category_id)

    await state.set_state(AddKeysState.receiving_keys)
    cat_name = config.CATEGORIES[category_id]["name"]
    await callback.message.edit_text(
        f"➕ Добавление ключей: {cat_name}\n\n"
        "Отправьте ключи (каждый ключ с новой строки):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_cancel")]
        ])
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data in ["admin_cancel", "delete_cancel"])
async def admin_cancel(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🔐 Панель администратора\n\nВыберите действие:",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()

@dp.message(AddKeysState.receiving_keys)
async def admin_add_keys_receive(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ Нет доступа")
        await state.clear()
        return

    data = await state.get_data()
    category_id = data["category_id"]

    keys = message.text.strip().split("\n")
    added_count = db.add_keys(keys, category_id)

    cat_name = config.CATEGORIES[category_id]["name"]
    await message.answer(
        f"✅ Успешно добавлено {added_count} ключей категории \"{cat_name}\"",
        reply_markup=get_admin_keyboard()
    )
    await state.clear()

# Delete keys handlers
@dp.callback_query(lambda c: c.data == "admin_delete_keys")
async def admin_delete_keys_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Нет доступа")
        return

    await state.set_state(DeleteKeysState.choosing_category)
    await callback.message.edit_text(
        "➖ Удаление ключей\n\nВыберите категорию:",
        reply_markup=get_categories_keyboard()
    )
    await callback.answer()

@dp.callback_query(DeleteKeysState.choosing_category)
async def admin_delete_keys_category(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Нет доступа")
        return

    if callback.data == "main_menu":
        await state.clear()
        await callback.message.edit_text(
            "🔐 Панель администратора\n\nВыберите действие:",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    category_id = callback.data.replace("category_", "")
    await state.update_data(category_id=category_id)

    await state.set_state(DeleteKeysState.viewing_keys)
    cat_name = config.CATEGORIES[category_id]["name"]

    keys = db.get_all_keys_by_category(category_id)

    if not keys:
        await callback.message.edit_text(
            f"➖ Категория \"{cat_name}\"\n\nВ этой категории нет ключей.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_cancel")]
            ])
        )
        await callback.answer()
        return

    text = f"➖ Категория \"{cat_name}\"\n\n"
    text += f"Всего ключей: {len(keys)}\n\n"

    # Show first 10 keys
    for i, key in enumerate(keys[:10], 1):
        status_emoji = "✅" if key["status"] == "available" else "🔴"
        text += f"{i}. {status_emoji} `{key['key_value'][:20]}...`\n"

    if len(keys) > 10:
        text += f"\n... и еще {len(keys) - 10} ключей"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Найти по значению", callback_data="delete_search_key")],
        [InlineKeyboardButton(text="🗑 Удалить все доступные", callback_data="delete_all_available")],
        [InlineKeyboardButton(text="🗑 Удалить все ключи", callback_data="delete_all_keys")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_cancel")]
    ])

    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(DeleteKeysState.viewing_keys)
async def admin_delete_keys_actions(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Нет доступа")
        return

    if callback.data == "admin_cancel":
        await state.clear()
        await callback.message.edit_text(
            "🔐 Панель администратора\n\nВыберите действие:",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    data = await state.get_data()
    category_id = data["category_id"]
    cat_name = config.CATEGORIES[category_id]["name"]

    if callback.data == "delete_all_available":
        deleted_count = db.delete_keys_by_category(category_id, status="available")
        await callback.message.edit_text(
            f"✅ Удалено {deleted_count} доступных ключей категории \"{cat_name}\"",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
        await callback.answer()
        return

    if callback.data == "delete_all_keys":
        await state.set_state(DeleteKeysState.deleting_key)
        await callback.message.edit_text(
            f"⚠️ Вы уверены, что хотите удалить ВСЕ ключи категории \"{cat_name}\"?\n\n"
            "Это действие нельзя отменить!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Да, удалить все", callback_data="confirm_delete_all")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="delete_cancel")]
            ])
        )
        await callback.answer()
        return

    if callback.data == "delete_search_key":
        await state.set_state(DeleteKeysState.searching_key)
        await callback.message.edit_text(
            "🔍 Поиск ключа\n\nВведите ключ или его часть для поиска:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Отмена", callback_data="delete_cancel")]
            ])
        )
        await callback.answer()
        return

@dp.callback_query(DeleteKeysState.deleting_key)
async def admin_delete_keys_confirm(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Нет доступа")
        return

    data = await state.get_data()
    category_id = data["category_id"]
    cat_name = config.CATEGORIES[category_id]["name"]

    if callback.data == "confirm_delete_all":
        deleted_count = db.delete_keys_by_category(category_id)
        await callback.message.edit_text(
            f"✅ Удалено {deleted_count} ключей категории \"{cat_name}\"",
            reply_markup=get_admin_keyboard()
        )
        await state.clear()
        await callback.answer()
        return

    if callback.data == "delete_cancel":
        await state.set_state(DeleteKeysState.viewing_keys)
        keys = db.get_all_keys_by_category(category_id)

        text = f"➖ Категория \"{cat_name}\"\n\n"
        text += f"Всего ключей: {len(keys)}\n\n"

        for i, key in enumerate(keys[:10], 1):
            status_emoji = "✅" if key["status"] == "available" else "🔴"
            text += f"{i}. {status_emoji} `{key['key_value'][:20]}...`\n"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Найти по значению", callback_data="delete_search_key")],
            [InlineKeyboardButton(text="🗑 Удалить все доступные", callback_data="delete_all_available")],
            [InlineKeyboardButton(text="🗑 Удалить все ключи", callback_data="delete_all_keys")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_cancel")]
        ])

        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
        await callback.answer()
        return

@dp.message(DeleteKeysState.searching_key)
async def admin_delete_keys_search(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("⛔ Нет доступа")
        await state.clear()
        return

    search_term = message.text.strip()
    key_data = db.search_key_by_value(search_term)

    if not key_data:
        await message.answer(
            f"❌ Ключ \"{search_term}\" не найден.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="delete_cancel")]
            ])
        )
        return

    cat_name = config.CATEGORIES[key_data["category_id"]]["name"]
    status_emoji = "✅" if key_data["status"] == "available" else "🔴"

    text = (
        f"🔍 Найден ключ:\n\n"
        f"Ключ: `{key_data['key_value']}`\n"
        f"Категория: {cat_name}\n"
        f"Статус: {status_emoji} {key_data['status']}\n"
        f"Добавлен: {key_data['created_at']}\n\n"
        "Удалить этот ключ?"
    )

    await state.update_data(key_id=key_data["id"], key_value=key_data["key_value"])
    await state.set_state(DeleteKeysState.deleting_key)

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да, удалить", callback_data="confirm_delete_single")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="delete_cancel")]
        ])
    )

@dp.callback_query(DeleteKeysState.deleting_key)
async def admin_delete_single_key(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Нет доступа")
        return

    if callback.data == "confirm_delete_single":
        data = await state.get_data()
        key_id = data["key_id"]
        key_value = data["key_value"]

        deleted = db.delete_key_by_id(key_id)

        if deleted:
            await callback.message.edit_text(
                f"✅ Ключ `{key_value}` успешно удален",
                parse_mode="Markdown",
                reply_markup=get_admin_keyboard()
            )
        else:
            await callback.message.edit_text(
                "❌ Ошибка при удалении ключа",
                reply_markup=get_admin_keyboard()
            )

        await state.clear()
        await callback.answer()
        return

@dp.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats_callback(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("⛔ Нет доступа")
        return

    stats = db.get_admin_stats()
    text = (
        "📊 Статистика\n\n"
        f"👥 Пользователей: {stats['total_users']}\n"
        f"💰 Продаж: {stats['total_purchases']}\n"
        f"💵 Выручка: {stats['total_revenue']:.2f}₽\n\n"
        "📦 Ключи по категориям:\n"
    )

    for cat_id, cat_info in config.CATEGORIES.items():
        total = stats['total_keys'].get(cat_id, 0)
        available = stats['available_keys'].get(cat_id, 0)
        issued = total - available
        text += f"\n{cat_info['name']}:\n"
        text += f"  Всего: {total}\n"
        text += f"  Доступно: {available}\n"
        text += f"  Выдано: {issued}\n"

    await callback.message.edit_text(text, reply_markup=get_admin_keyboard())
    await callback.answer()

# Purchase handlers
@dp.callback_query(lambda c: c.data == "buy_key")
async def buy_key_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(PurchaseState.choosing_category)
    await callback.message.edit_text(
        "🛒 Покупка ключа\n\nВыберите категорию:",
        reply_markup=get_categories_keyboard()
    )
    await callback.answer()

@dp.callback_query(PurchaseState.choosing_category)
async def buy_key_category(callback: types.CallbackQuery, state: FSMContext):
    if callback.data == "main_menu":
        await state.clear()
        await callback.message.edit_text(
            "👋 Главное меню\n\nВыберите действие:",
            reply_markup=get_main_keyboard()
        )
        await callback.answer()
        return

    category_id = callback.data.replace("category_", "")
    cat_info = config.CATEGORIES[category_id]

    # Check availability
    available_count = db.get_available_keys_count(category_id)
    if available_count == 0:
        await callback.message.edit_text(
            f"❌ Товар временно закончился\n\n"
            f"Категория \"{cat_info['name']}\" недоступна.\n\n"
            "Попробуйте позже или свяжитесь с поддержкой.",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        await callback.answer()
        return

    await state.update_data(category_id=category_id)

    # Create invoice (Telegram Payments)
    if config.PAYMENT_PROVIDER_TOKEN:
        await create_invoice(callback, category_id, cat_info, state)
    else:
        # Alternative payment method (CryptoBot or manual)
        await callback.message.edit_text(
            f"💳 Оплата: {cat_info['name']}\n\n"
            f"Сумма: {cat_info['price']}₽\n\n"
            "⚠️ Telegram Payments не настроен.\n"
            "Для оплаты свяжитесь с админом: @admin",
            reply_markup=get_main_keyboard()
        )
        await state.clear()
        await callback.answer()

async def create_invoice(callback: types.CallbackQuery, category_id: str, cat_info: dict, state: FSMContext):
    """Create Telegram Payment invoice"""
    title = f"Ключ SKTrade ({cat_info['name']})"
    description = f"Ключ для программы SKTrade на срок {cat_info['name']}"
    payload = f"purchase_{category_id}"
    currency = "RUB"
    prices = [LabeledPrice(label=f"{cat_info['name']}", amount=cat_info['price'] * 100)]  # in kopecks

    await callback.message.edit_text(
        f"💳 Оплата: {cat_info['name']}\n\n"
        f"Сумма: {cat_info['price']}₽\n\n"
        "Нажмите кнопку ниже для оплаты:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", pay=True)],
            [InlineKeyboardButton(text="🔙 Отмена", callback_data="main_menu")]
        ])
    )

    await callback.answer()

    # Send invoice
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=title,
        description=description,
        payload=payload,
        provider_token=config.PAYMENT_PROVIDER_TOKEN,
        currency=currency,
        prices=prices,
        start_parameter="sktrade_payment"
    )

    await state.clear()

@dp.pre_checkout_query()
async def pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    """Process pre-checkout query"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(lambda m: m.successful_payment)
async def successful_payment(message: types.Message):
    """Handle successful payment"""
    user_id = message.from_user.id
    payment = message.successful_payment
    category_id = payment.invoice_payload.replace("purchase_", "")

    # Get available key
    key_data = db.get_available_key(category_id)
    if not key_data:
        await message.answer(
            "❌ Произошла ошибка. Ключи закончились.\n"
            "Свяжитесь с поддержкой для возврата средств."
        )
        return

    # Issue key to user
    db.issue_key(key_data["id"], user_id)

    # Create purchase record
    purchase_id = db.create_purchase(
        user_id=user_id,
        key_id=key_data["id"],
        category_id=category_id,
        amount=payment.total_amount / 100,  # convert from kopecks
        payment_id=payment.telegram_payment_charge_id
    )

    # Complete purchase
    db.complete_purchase(purchase_id)

    cat_name = config.CATEGORIES[category_id]["name"]

    text = (
        "✅ Оплата прошла успешно!\n\n"
        f"🔑 Ваш ключ: `{key_data['key_value']}`\n"
        f"Категория: {cat_name}\n\n"
        "📋 Инструкция по активации:\n"
        "1. Скачайте программу SKTrade\n"
        "2. Запустите программу\n"
        "3. Введите полученный ключ в поле активации\n"
        "4. Нажмите кнопку \"Активировать\"\n\n"
        "🎉 Пользуйтесь!"
    )

    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
