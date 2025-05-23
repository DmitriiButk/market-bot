from typing import List, Dict, Any, Optional
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ...db import get_product, get_cart_items, add_item_to_cart, remove_item_from_cart, clear_user_cart
from ...utils.config import QUANTITY_CALLBACK_PREFIX, ADD_TO_CART_PREFIX, MAX_PRODUCT_QUANTITY, QUANTITY_ERROR, \
    SUCCESS_MESSAGE, CART_EMPTY_MESSAGE, REMOVE_PREFIX, CLEAR_CART_CALLBACK
from ...utils.states import CatalogStates
from .base import catalog_router, safe_callback_execution, CART_CALLBACK, CATALOG_CALLBACK, MAIN_MENU_CALLBACK
from ...utils.logger import logger


def get_product_added_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для сообщения об успешном добавлении товара в корзину.

    Клавиатура содержит три кнопки: переход в корзину, возврат в каталог
    и возврат в главное меню.

    Returns:
        InlineKeyboardMarkup: Клавиатура с тремя кнопками навигации
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Перейти в корзину", callback_data=CART_CALLBACK)],
        [InlineKeyboardButton(text="🔄 Продолжить покупки", callback_data=CATALOG_CALLBACK)],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU_CALLBACK)]
    ])


def get_quantity_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для выбора количества товара при добавлении в корзину.

    Клавиатура содержит пять фиксированных вариантов количества (1, 2, 3, 5, 10),
    опцию ввода нестандартного количества и кнопку отмены.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками выбора количества
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data=f"{QUANTITY_CALLBACK_PREFIX}1"),
            InlineKeyboardButton(text="2", callback_data=f"{QUANTITY_CALLBACK_PREFIX}2"),
            InlineKeyboardButton(text="3", callback_data=f"{QUANTITY_CALLBACK_PREFIX}3"),
        ],
        [
            InlineKeyboardButton(text="5", callback_data=f"{QUANTITY_CALLBACK_PREFIX}5"),
            InlineKeyboardButton(text="10", callback_data=f"{QUANTITY_CALLBACK_PREFIX}10"),
            InlineKeyboardButton(text="Другое", callback_data=f"{QUANTITY_CALLBACK_PREFIX}other"),
        ],
        [InlineKeyboardButton(text="↩️ Отмена", callback_data=CATALOG_CALLBACK)]
    ])


def get_cart_empty_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру для пустой корзины.

    Клавиатура содержит кнопки перехода в каталог товаров и возврата в главное меню,
    которые отображаются пользователю при пустой корзине.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками навигации
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛍 Перейти в каталог", callback_data=CATALOG_CALLBACK)],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU_CALLBACK)]
    ])


@catalog_router.callback_query(lambda c: c.data.startswith(ADD_TO_CART_PREFIX))
async def add_to_cart(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает запрос на добавление товара в корзину и запрашивает количество.

    Args:
        callback: Объект callback_query с данными в формате "add_to_cart_{product_id}"
        state: Объект состояния FSM для сохранения ID товара между запросами
    """

    async def request_quantity():
        try:
            product_id: int = int(callback.data.split("_")[3])
            product: Dict[str, Any] = await get_product(product_id)

            if not product:
                logger.error(
                    f"Товар с ID {product_id} не найден при добавлении в корзину пользователем ID:{callback.from_user.id}")
                await callback.answer("Товар не найден")
                return

            await state.update_data(product_id=product_id)

            await callback.message.edit_text(
                f"<b>{product['name']}</b>\n"
                f"Цена: <b>{product['price']} ₽</b>\n\n"
                f"Укажите количество:",
                reply_markup=get_quantity_keyboard(),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при запросе количества товара пользователем ID:{callback.from_user.id}: {e}")
            raise

    await safe_callback_execution(
        callback,
        request_quantity,
        "Произошла ошибка при добавлении товара в корзину"
    )
    await callback.answer()


@catalog_router.callback_query(lambda c: c.data.startswith(QUANTITY_CALLBACK_PREFIX))
async def process_quantity(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обрабатывает выбор количества товара через кнопки быстрого выбора.

    Args:
        callback: Объект callback_query с данными в формате "quantity_{число}"
        state: Объект состояния FSM для получения ID товара
    """

    async def handle_quantity_selection():
        quantity: str = callback.data.split("_")[1]
        data: Dict[str, Any] = await state.get_data()
        product_id: Optional[int] = data.get("product_id")

        if not product_id:
            await callback.answer("Ошибка: не указан товар")
            return

        if quantity == "other":
            await callback.message.edit_text(
                "Введите желаемое количество (от 1 до 100):",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="↩️ Отмена", callback_data=CATALOG_CALLBACK)]
                ])
            )
            await state.set_state(CatalogStates.waiting_for_quantity)
            return

        await add_product_to_cart(callback, product_id, int(quantity), state)

    await safe_callback_execution(
        callback,
        handle_quantity_selection,
        "Произошла ошибка при выборе количества"
    )
    await callback.answer()


@catalog_router.message(CatalogStates.waiting_for_quantity)
async def process_custom_quantity(message: types.Message, state: FSMContext) -> None:
    """
    Обрабатывает пользовательский ввод количества товара.

    Args:
        message: Объект сообщения с текстовым вводом пользователя
        state: Объект состояния FSM, содержащий ID выбранного товара
    """
    try:
        data: Dict[str, Any] = await state.get_data()
        product_id: Optional[int] = data.get("product_id")
        user_id: int = message.from_user.id

        if not product_id:
            logger.error(f"Ошибка: отсутствует product_id в состоянии для пользователя ID:{user_id}")
            await message.reply("Ошибка: не указан товар")
            await state.clear()
            return

        if not message.text.isdigit():
            logger.info(f"Пользователь ID:{user_id} ввел некорректное значение количества: '{message.text}'")
            await message.reply(
                "Пожалуйста, введите только число (от 1 до 100)."
            )
            return

        quantity: int = int(message.text)
        if quantity < 1 or quantity > MAX_PRODUCT_QUANTITY:
            logger.info(f"Пользователь ID:{user_id} ввел недопустимое количество: {quantity}")
            await message.reply(
                QUANTITY_ERROR.format(max_quantity=MAX_PRODUCT_QUANTITY)
            )
            return

        await add_product_to_cart_message(message, product_id, quantity, state)

    except Exception as e:
        logger.error(
            f"Ошибка при обработке пользовательского количества для пользователя ID:{message.from_user.id}: {e}")
        await message.reply("Произошла ошибка при обработке количества")
        await state.clear()


async def add_product_to_cart(callback: types.CallbackQuery, product_id: int, quantity: int, state: FSMContext) -> None:
    """
    Добавляет товар в корзину пользователя при выборе через callback.

    Получает информацию о товаре из базы данных, добавляет товар в корзину пользователя
    и отображает сообщение об успешном добавлении. Обрабатывает возможные ошибки
    и в любом случае очищает состояние FSM.

    Args:
        callback: Объект callback_query, содержащий информацию о пользователе
        product_id: ID товара для добавления в корзину
        quantity: Количество товара для добавления
        state: Объект состояния FSM для хранения промежуточных данных

    Raises:
        Exception: При ошибках доступа к базе данных или выполнения запроса
    """
    try:
        user_id: int = callback.from_user.id
        product: Dict[str, Any] = await get_product(product_id)

        await add_item_to_cart(user_id, product_id, quantity)

        await callback.message.edit_text(
            SUCCESS_MESSAGE.format(product=f"<b>{product['name']}</b>", quantity=quantity),
            reply_markup=get_product_added_keyboard(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(
            f"Ошибка при добавлении товара ID:{product_id} в корзину пользователем ID:{callback.from_user.id}: {e}")
        await callback.answer("Произошла ошибка при добавлении в корзину")

    finally:
        await state.clear()


async def add_product_to_cart_message(message: types.Message, product_id: int, quantity: int,
                                      state: FSMContext) -> None:
    """
    Добавляет товар в корзину пользователя при вводе через текстовое сообщение.

    Функция аналогична add_product_to_cart, но работает с объектом message вместо callback.
    Получает информацию о товаре, добавляет товар в корзину пользователя и отображает
    сообщение об успешном добавлении. Обрабатывает возможные ошибки и очищает состояние FSM.

    Args:
        message: Объект сообщения от пользователя с информацией о пользователе
        product_id: ID товара для добавления в корзину
        quantity: Количество товара для добавления
        state: Объект состояния FSM для хранения промежуточных данных

    Raises:
        Exception: При ошибках доступа к базе данных или выполнения запроса
    """
    try:
        user_id: int = message.from_user.id
        product: Dict[str, Any] = await get_product(product_id)

        await add_item_to_cart(user_id, product_id, quantity)

        await message.answer(
            SUCCESS_MESSAGE.format(product=f"<b>{product['name']}</b>", quantity=quantity),
            reply_markup=get_product_added_keyboard(),
            parse_mode="HTML"
        )

    except Exception as e:
        logger.error(
            f"Ошибка при добавлении товара ID:{product_id} в корзину пользователем ID:{message.from_user.id}: {e}")
        await message.reply("Произошла ошибка при добавлении в корзину")

    finally:
        await state.clear()


@catalog_router.callback_query(lambda c: c.data == CART_CALLBACK)
async def show_cart(callback: types.CallbackQuery) -> None:
    """
    Отображает содержимое корзины пользователя.

    Args:
        callback: Объект callback_query от нажатия на кнопку корзины
    """

    async def display_cart():
        try:
            user_id: int = callback.from_user.id
            cart_items: List[Dict[str, Any]] = await get_cart_items(user_id)

            if not cart_items:
                await callback.message.edit_text(
                    CART_EMPTY_MESSAGE,
                    reply_markup=get_cart_empty_keyboard()
                )
                return

            cart_text: str = "<b>Ваша корзина:</b>\n\n"
            total_sum: float = 0

            for item in cart_items:
                item_total: float = item['price'] * item['quantity']
                cart_text += f"• {item['name']} - {item['price']} ₽ x {item['quantity']} = {item_total} ₽\n"
                total_sum += item_total

            cart_text += f"\n<b>Итого: {total_sum} ₽</b>"

            keyboard_items: List[List[InlineKeyboardButton]] = [
                [InlineKeyboardButton(
                    text=f"❌ Удалить {item['name']}",
                    callback_data=f"{REMOVE_PREFIX}{item['id']}"
                )] for item in cart_items
            ]

            kb: InlineKeyboardMarkup = InlineKeyboardMarkup(
                inline_keyboard=keyboard_items + [
                    [InlineKeyboardButton(text="🗑 Очистить корзину", callback_data=CLEAR_CART_CALLBACK)],
                    [InlineKeyboardButton(text="💳 Оформить заказ", callback_data="checkout")],
                    [InlineKeyboardButton(text="🛍 Вернуться в каталог", callback_data=CATALOG_CALLBACK)],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU_CALLBACK)]
                ]
            )

            await callback.message.edit_text(cart_text, reply_markup=kb, parse_mode="HTML")

        except Exception as e:
            logger.error(f"Ошибка при отображении корзины пользователя ID:{callback.from_user.id}: {e}")
            raise

    await safe_callback_execution(
        callback,
        display_cart,
        "Произошла ошибка при загрузке корзины"
    )
    await callback.answer()


@catalog_router.callback_query(lambda c: c.data.startswith(REMOVE_PREFIX))
async def remove_from_cart(callback: types.CallbackQuery) -> None:
    """
    Удаляет выбранный товар из корзины пользователя.

    Args:
        callback: Объект callback_query с ID элемента в формате "remove_{cart_item_id}"
    """

    async def remove_item():
        cart_item_id: int = int(callback.data.split("_")[1])
        user_id: int = callback.from_user.id

        try:
            await remove_item_from_cart(user_id, cart_item_id)
            await callback.answer("Товар удален из корзины")

            await show_cart(callback)
        except Exception as e:
            logger.error(f"Ошибка при удалении товара ID:{cart_item_id} из корзины пользователя ID:{user_id}: {e}")
            raise

    await safe_callback_execution(
        callback,
        remove_item,
        "Произошла ошибка при удалении товара"
    )


@catalog_router.callback_query(lambda c: c.data == CLEAR_CART_CALLBACK)
async def clear_cart(callback: types.CallbackQuery) -> None:
    """
    Очищает корзину пользователя полностью.

    Args:
        callback: Объект callback_query от кнопки "Очистить корзину"
    """

    async def clear_all_items():
        user_id: int = callback.from_user.id

        try:
            await clear_user_cart(user_id)
            await callback.answer("Корзина очищена")

            await show_cart(callback)
        except Exception as e:
            logger.error(f"Ошибка при очистке корзины пользователя ID:{user_id}: {e}")
            raise

    await safe_callback_execution(
        callback,
        clear_all_items,
        "Произошла ошибка при очистке корзины"
    )
