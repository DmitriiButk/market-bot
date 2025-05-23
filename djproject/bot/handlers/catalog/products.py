from typing import Optional, List, Dict, Any

from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .base import catalog_router, safe_callback_execution, get_back_button
from ...db import get_products, get_category_name, get_subcategory_name, get_product
from ...utils.config import PRODUCTS_PER_PAGE
from ...utils.logger import logger


async def show_products(callback: types.CallbackQuery, category_id: Optional[int] = None,
                        subcategory_id: Optional[int] = None, page: int = 1) -> None:
    """
    Отображает список товаров с пагинацией для указанной категории или подкатегории.

    Загружает товары из базы данных с учетом фильтрации по категории/подкатегории
    и настраивает их отображение на странице с пагинацией.

    Args:
        callback: Объект callback_query для взаимодействия с сообщением пользователя
        category_id: ID категории для фильтрации товаров
        subcategory_id: ID подкатегории для фильтрации товаров
        page: Номер страницы для пагинации (начиная с 1)
    """
    try:
        products: List[Dict[str, Any]]
        total_products: int
        products, total_products = await get_products(
            category_id=category_id,
            subcategory_id=subcategory_id,
            page=page,
            per_page=PRODUCTS_PER_PAGE
        )

        if not products:
            back_button: str = get_back_button(subcategory_id, category_id)

            await callback.message.edit_text(
                "В этой категории пока нет товаров.",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data=back_button)],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ])
            )
            return

        title: str = "Товары:"
        if category_id:
            title = f"Товары в категории «{await get_category_name(category_id)}»:"
        elif subcategory_id:
            title = f"Товары в подкатегории «{await get_subcategory_name(subcategory_id)}»:"

        total_pages: int = (total_products + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE
        pagination_buttons: List[List[InlineKeyboardButton]] = []

        if total_pages > 1:
            pagination_row: List[InlineKeyboardButton] = []

            if page > 1:
                pagination_row.append(InlineKeyboardButton(
                    text="⬅️",
                    callback_data=f"products_page_{category_id or 0}_{subcategory_id or 0}_{page - 1}"
                ))

            pagination_row.append(InlineKeyboardButton(
                text=f"{page}/{total_pages}",
                callback_data="ignore"
            ))

            if page < total_pages:
                pagination_row.append(InlineKeyboardButton(
                    text="➡️",
                    callback_data=f"products_page_{category_id or 0}_{subcategory_id or 0}_{page + 1}"
                ))

            pagination_buttons.append(pagination_row)

        back_button: str = get_back_button(subcategory_id, category_id)

        product_buttons: List[List[InlineKeyboardButton]] = [
            [InlineKeyboardButton(
                text=f"{product['name']} - {product['price']} ₽",
                callback_data=f"product_{product['id']}"
            )] for product in products
        ]

        kb: InlineKeyboardMarkup = InlineKeyboardMarkup(
            inline_keyboard=product_buttons + pagination_buttons + [
                [InlineKeyboardButton(text="◀️ Назад", callback_data=back_button)],
                [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ]
        )

        await callback.message.edit_text(title, reply_markup=kb)

    except Exception as e:
        logger.error(
            f"Ошибка при отображении товаров: {e} | "
            f"Категория: {category_id}, Подкатегория: {subcategory_id}, Страница: {page}"
        )
        await callback.answer("Произошла ошибка при загрузке товаров")


@catalog_router.callback_query(lambda c: c.data.startswith("products_page_"))
async def handle_products_pagination(callback: types.CallbackQuery) -> None:
    """
    Обрабатывает пагинацию списка товаров при навигации по страницам.

    Args:
        callback: Объект callback_query с данными о страницах в формате
                "products_page_{category_id}_{subcategory_id}_{page}"
    """

    async def process_pagination():
        try:
            _, category_id, subcategory_id, page_str = callback.data.split("_")[1:]

            category_id_int: Optional[int] = int(category_id) if category_id != '0' else None
            subcategory_id_int: Optional[int] = int(subcategory_id) if subcategory_id != '0' else None
            page: int = int(page_str)

            await show_products(callback, category_id_int, subcategory_id_int, page)
        except ValueError as e:
            logger.error(f"Ошибка при обработке параметров пагинации: {e} | Данные: {callback.data}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при навигации по товарам: {e}")
            raise

    await safe_callback_execution(
        callback,
        process_pagination,
        "Произошла ошибка при навигации по товарам"
    )


@catalog_router.callback_query(lambda c: c.data.startswith("product_"))
async def show_product_detail(callback: types.CallbackQuery) -> None:
    """
    Отображает детальную информацию о выбранном товаре.

    Args:
        callback: Объект callback_query с данными о товаре в формате "product_{product_id}"
    """

    async def display_product():
        try:
            product_id: int = int(callback.data.split("_")[1])
            product: Dict[str, Any] = await get_product(product_id)

            if not product:
                logger.error(f"Товар с ID {product_id} не найден при запросе детальной информации")
                await callback.answer("Товар не найден")
                return

            category_id = product.get('category_id')
            subcategory_id = product.get('subcategory_id')
            back_data = f"back_to_products_{category_id or 0}_{subcategory_id or 0}"

            kb: InlineKeyboardMarkup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🛒 Добавить в корзину",
                                          callback_data=f"add_to_cart_{product_id}")],
                    [InlineKeyboardButton(text="◀️ Назад к товарам", callback_data=back_data)],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ]
            )

            description = (f"<b>{product['name']}</b>\n\n"
                           f"{product['description']}\n\n"
                           f"<b>Цена: {product['price']} ₽</b>")

            if product.get('image'):
                await callback.message.delete()
                await callback.message.answer_photo(
                    photo=product['image'],
                    caption=description,
                    reply_markup=kb,
                    parse_mode="HTML"
                )
            else:
                await callback.message.edit_text(
                    description,
                    reply_markup=kb,
                    parse_mode="HTML"
                )

        except ValueError as e:
            logger.error(f"Ошибка при получении ID товара: {e} | Данные: {callback.data}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при отображении детальной информации о товаре: {e} | Данные: {callback.data}")
            raise

    await safe_callback_execution(
        callback,
        display_product,
        "Произошла ошибка при загрузке информации о товаре"
    )
    await callback.answer()


@catalog_router.callback_query(lambda c: c.data.startswith("back_to_products_"))
async def back_to_products(callback: types.CallbackQuery) -> None:
    """
    Обрабатывает возврат к списку товаров категории или подкатегории.

    Args:
        callback: Объект callback_query с данными в формате
                "back_to_products_{category_id}_{subcategory_id}"
    """

    async def navigate_back():
        try:
            parts: List[str] = callback.data.split("_")
            category_id: Optional[int] = int(parts[3]) if parts[3] != '0' else None
            subcategory_id: Optional[int] = int(parts[4]) if len(parts) > 4 and parts[4] != '0' else None

            await show_products(callback, category_id, subcategory_id, page=1)
        except IndexError as e:
            logger.error(f"Ошибка в формате callback-данных: {e} | Данные: {callback.data}")
            raise
        except ValueError as e:
            logger.error(f"Ошибка при получении ID категории или подкатегории: {e} | Данные: {callback.data}")
            raise
        except Exception as e:
            logger.error(f"Ошибка при возврате к списку товаров: {e}")
            raise

    await safe_callback_execution(
        callback,
        navigate_back,
        "Произошла ошибка при возврате к списку товаров"
    )
