import uuid
import re
from typing import Dict, Any, List

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ...utils.states import CatalogStates
from ...services.payments import TinkoffPayment
from ...utils.config import TINKOFF_TERMINAL_KEY, TINKOFF_PASSWORD
from .base import catalog_router, safe_callback_execution
from ...db import get_cart_items, create_order, save_order_to_google_sheets, update_order_payment_info
from ...utils.logger import logger


@catalog_router.callback_query(lambda c: c.data == "checkout")
async def checkout(callback: types.CallbackQuery) -> None:
    """
    Обрабатывает запрос на оформление заказа.

    Args:
        callback: Объект callback_query от кнопки "Оформить заказ"
    """

    async def start_checkout():
        try:
            user_id: int = callback.from_user.id
            cart_items: List[Dict[str, Any]] = await get_cart_items(user_id)

            if not cart_items:
                await callback.answer("Ваша корзина пуста")
                return

            await callback.message.edit_text(
                "Для оформления заказа нам нужны ваши данные для доставки.\n"
                "Выберите действие:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✏️ Ввести данные", callback_data="enter_delivery_data")],
                    [InlineKeyboardButton(text="◀️ Назад в корзину", callback_data="cart")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ])
            )
        except Exception as e:
            logger.error(f"Ошибка при запуске оформления заказа пользователем ID:{callback.from_user.id}: {e}")
            raise

    await safe_callback_execution(
        callback,
        start_checkout,
        "Произошла ошибка при оформлении заказа"
    )
    await callback.answer()


@catalog_router.callback_query(lambda c: c.data == "enter_delivery_data")
async def enter_delivery_data(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Запрашивает у пользователя имя для оформления заказа.

    Args:
        callback: Объект callback_query от кнопки "Ввести данные"
        state: Объект состояния FSM для сохранения данных пользователя
    """

    async def request_name():
        try:
            await callback.message.edit_text(
                "Пожалуйста, введите ваше имя:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Отмена", callback_data="cart")]
                ])
            )
            await state.set_state(CatalogStates.waiting_for_name)
        except Exception as e:
            logger.error(f"Ошибка при запросе имени пользователя ID:{callback.from_user.id}: {e}")
            raise

    await safe_callback_execution(
        callback,
        request_name,
        "Произошла ошибка при запросе данных"
    )
    await callback.answer()


@catalog_router.message(CatalogStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод имени пользователя при оформлении заказа.

    Args:
        message: Сообщение пользователя с именем
        state: Состояние FSM для хранения данных заказа
    """
    await state.update_data(name=message.text)
    await message.answer(
        "Спасибо! Теперь введите ваш номер телефона:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cart")]
        ])
    )
    await state.set_state(CatalogStates.waiting_for_phone)


@catalog_router.message(CatalogStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод номера телефона с валидацией.

    Args:
        message: Сообщение пользователя с номером телефона
        state: Состояние FSM для хранения данных заказа
    """
    try:
        phone: str = message.text.strip()
        cleaned_phone: str = re.sub(r'\D', '', phone)

        if not re.match(r'^(7|8)?\d{10}$', cleaned_phone):
            logger.error(f"Пользователь ID:{message.from_user.id} ввел некорректный номер телефона: {phone}")
            await message.answer(
                "Введен некорректный номер телефона. Пожалуйста, введите номер в формате +7XXXXXXXXXX или 8XXXXXXXXXX:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="Отмена", callback_data="cart")]
                ])
            )
            return

        if cleaned_phone.startswith('8'):
            cleaned_phone = '+7' + cleaned_phone[1:]
        elif cleaned_phone.startswith('7'):
            cleaned_phone = '+' + cleaned_phone
        else:
            cleaned_phone = '+7' + cleaned_phone

        await state.update_data(phone=cleaned_phone)
        await message.answer(
            "Спасибо! Теперь введите адрес доставки:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Отмена", callback_data="cart")]
            ])
        )
        await state.set_state(CatalogStates.waiting_for_address)
    except Exception as e:
        logger.error(f"Ошибка при обработке телефона пользователя ID:{message.from_user.id}: {e}")
        await message.reply("Произошла ошибка. Пожалуйста, попробуйте позже.")
        await state.clear()


@catalog_router.message(CatalogStates.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext) -> None:
    """
    Обрабатывает ввод адреса доставки и завершает оформление заказа.

    Args:
        message: Сообщение пользователя с адресом доставки
        state: Состояние FSM для хранения данных заказа
    """
    wait_message = None
    try:
        wait_message = await message.answer("⏳ Заказ формируется, пожалуйста, подождите...")

        user_data: Dict[str, Any] = await state.update_data(address=message.text)
        user_id: int = message.from_user.id

        cart_items: List[Dict[str, Any]] = await get_cart_items(user_id)

        if not cart_items:
            logger.error(f"Пользователь ID:{user_id} пытается оформить заказ с пустой корзиной")
            await wait_message.delete()
            await message.answer("Ваша корзина пуста. Заказ не может быть оформлен.")
            await state.clear()
            return

        order_details: str = "Ваш заказ:\n\n"
        total_sum: float = 0

        for item in cart_items:
            item_total: float = item['price'] * item['quantity']
            order_details += f"• {item['name']} - {item['price']} ₽ x {item['quantity']} = {item_total} ₽\n"
            total_sum += item_total

        order_details += f"\nИтого: {total_sum} ₽\n\n"
        order_details += f"Имя: {user_data['name']}\n"
        order_details += f"Телефон: {user_data['phone']}\n"
        order_details += f"Адрес доставки: {user_data['address']}"

        try:
            order_id: int = await create_order(
                user_id=user_id,
                items=cart_items,
                name=user_data['name'],
                phone=user_data['phone'],
                address=user_data['address'],
                total_amount=total_sum
            )
        except Exception as db_error:
            logger.error(f"Ошибка при сохранении заказа в БД для пользователя ID:{user_id}: {db_error}")
            raise

        try:
            await save_order_to_google_sheets(order_id)
        except Exception as sheets_error:
            logger.error(f"Ошибка при сохранении заказа #{order_id} в Google Sheets: {sheets_error}")

        try:
            payment_system = TinkoffPayment(
                terminal_key=TINKOFF_TERMINAL_KEY,
                password=TINKOFF_PASSWORD
            )

            payment_id: str = f"order_{order_id}_{uuid.uuid4().hex[:8]}"
            payment_result: Dict[str, Any] = await payment_system.create_payment(
                order_id=payment_id,
                amount=total_sum,
                description=f"Заказ #{order_id} в нашем магазине",
                customer_phone=user_data['phone'],
                success_url="https://t.me/your_bot_username"  # URL бота
            )
        except Exception as payment_error:
            logger.error(f"Ошибка платежной системы при создании платежа для заказа #{order_id}: {payment_error}")
            raise

        await wait_message.delete()
        wait_message = None

        if payment_result.get("Success"):
            payment_url: str = payment_result.get("PaymentURL")

            try:
                await update_order_payment_info(
                    order_id=order_id,
                    payment_id=payment_id,
                    payment_url=payment_url
                )
            except Exception as update_error:
                logger.error(f"Ошибка при сохранении информации о платеже для заказа #{order_id}: {update_error}")

            await message.answer(
                f"Заказ #{order_id} успешно создан!\n\n"
                f"Для оплаты заказа на сумму {total_sum} ₽, пожалуйста, перейдите по ссылке ниже:\n",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💳 Оплатить заказ", url=payment_url)],
                    [InlineKeyboardButton(text="🛍 Вернуться в каталог", callback_data="catalog")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ])
            )
        else:
            logger.error(f"Ошибка платежного шлюза для заказа #{order_id}: {payment_result}")
            await message.answer(
                f"Заказ создан, но возникла проблема с платежным шлюзом.\n"
                f"Наш менеджер свяжется с вами для уточнения деталей оплаты.\n\n"
                f"Детали заказа:\n{order_details}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🛍 Вернуться в каталог", callback_data="catalog")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
                ])
            )

    except Exception as e:
        logger.error(f"Критическая ошибка при оформлении заказа пользователем ID:{message.from_user.id}: {e}")
        if wait_message:
            try:
                await wait_message.delete()
            except Exception as delete_error:
                logger.error(f"Ошибка при удалении сообщения об ожидании: {delete_error}")

        await message.answer(
            "Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте позже.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🛒 Вернуться в корзину", callback_data="cart")],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
            ])
        )

    await state.clear()
