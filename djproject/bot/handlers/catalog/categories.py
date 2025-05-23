from typing import List, Dict, Any
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .products import show_products
from .base import catalog_router, safe_callback_execution
from ...db import get_product_categories, get_subcategories, get_category_name
from ...utils.logger import logger


@catalog_router.callback_query(lambda c: c.data == "catalog")
async def show_categories(callback: types.CallbackQuery) -> None:
    """
    Отображает список доступных категорий товаров в каталоге.

    Получает список категорий из базы данных и формирует интерактивное меню
    с кнопками для навигации по категориям. Если категории отсутствуют в базе,
    показывает соответствующее сообщение.

    Args:
        callback: Объект callback_query, полученный при нажатии кнопки "Каталог"

    Raises:
        Exception: При ошибке получения данных из БД или обновления сообщения
    """
    user_id = callback.from_user.id

    async def display_categories():
        try:
            categories: List[Dict[str, Any]] = await get_product_categories()

            if not categories:
                await callback.message.edit_text(
                    "В каталоге пока нет категорий товаров.",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                    ])
                )
                return

            kb: InlineKeyboardMarkup = InlineKeyboardMarkup(
                inline_keyboard=[
                                    [InlineKeyboardButton(text=category['name'],
                                                          callback_data=f"category_{category['id']}")]
                                    for category in categories
                                ] + [
                                    [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                                ]
            )

            await callback.message.edit_text("Выберите категорию товаров:", reply_markup=kb)
        except Exception as e:
            logger.error(f"Ошибка при загрузке категорий для пользователя {user_id}: {e}")
            raise

    await safe_callback_execution(
        callback,
        display_categories,
        "Произошла ошибка при загрузке категорий"
    )
    await callback.answer()


@catalog_router.callback_query(lambda c: c.data.startswith("category_"))
async def show_subcategories_or_products(callback: types.CallbackQuery) -> None:
    """
    Обрабатывает выбор категории и отображает подкатегории или товары.

    Извлекает ID категории из данных callback, затем проверяет наличие подкатегорий
    в выбранной категории. Если подкатегории есть - отображает их списком с интерактивными
    кнопками. Если подкатегорий нет - напрямую отображает товары из выбранной категории.

    Args:
        callback: Объект callback_query, содержащий информацию о выбранной категории
                 в формате "category_{category_id}"

    Raises:
        ValueError: При невозможности преобразовать ID категории в число
        Exception: При ошибке получения данных или обновления сообщения
    """
    user_id = callback.from_user.id
    category_id = int(callback.data.split("_")[1])

    async def process_category():
        try:
            subcategories: List[Dict[str, Any]] = await get_subcategories(category_id)
            category_name: str = await get_category_name(category_id)

            if subcategories:
                kb: InlineKeyboardMarkup = InlineKeyboardMarkup(
                    inline_keyboard=[
                                        [InlineKeyboardButton(text=subcat['name'],
                                                              callback_data=f"subcat_{subcat['id']}")]
                                        for subcat in subcategories
                                    ] + [
                                        [InlineKeyboardButton(text="◀️ Назад к категориям", callback_data="catalog")],
                                        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                                    ]
                )

                await callback.message.edit_text(f"Подкатегории в «{category_name}»:", reply_markup=kb)
                return

            await show_products(callback, category_id=category_id)

        except Exception as e:
            logger.error(
                f"Ошибка при загрузке подкатегорий для категории ID:{category_id}, пользователь ID:{user_id}: {e}")
            raise

    await safe_callback_execution(
        callback,
        process_category,
        "Произошла ошибка при загрузке подкатегорий"
    )
    await callback.answer()


@catalog_router.callback_query(lambda c: c.data.startswith("subcat_"))
async def show_subcategory_products(callback: types.CallbackQuery) -> None:
    """
    Обрабатывает запрос на отображение товаров из выбранной подкатегории.

    Args:
        callback: Объект callback_query, содержащий информацию о выбранной подкатегории
                 в формате "subcat_{subcategory_id}"
    """
    user_id = callback.from_user.id
    subcategory_id = int(callback.data.split("_")[1])

    async def process_subcategory():
        try:
            await show_products(callback, subcategory_id=subcategory_id)
        except Exception as e:
            logger.error(
                f"Ошибка при загрузке товаров для подкатегории ID:{subcategory_id}, пользователь ID:{user_id}: {e}")
            raise

    await safe_callback_execution(
        callback,
        process_subcategory,
        "Произошла ошибка при загрузке товаров"
    )
