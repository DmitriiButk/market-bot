from typing import Optional, Callable
from aiogram import types, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import traceback

from djproject.bot.utils.config import MAIN_MENU_CALLBACK, CART_CALLBACK, CATALOG_CALLBACK, DEFAULT_ERROR_MESSAGE
from djproject.bot.utils.logger import logger

catalog_router = Router()


def create_error_keyboard() -> InlineKeyboardMarkup:
    """
    Создает стандартную клавиатуру для сообщений об ошибке.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками возврата в главное меню и корзину
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU_CALLBACK)],
        [InlineKeyboardButton(text="🛒 Корзина", callback_data=CART_CALLBACK)]
    ])


def get_back_button(subcategory_id: Optional[int] = None, category_id: Optional[int] = None) -> str:
    """
    Формирует callback_data для кнопки 'Назад' в зависимости от контекста.

    Args:
        subcategory_id: ID подкатегории, если нужно вернуться к родительской категории
        category_id: ID категории, если нужно вернуться к списку категорий

    Returns:
        str: callback_data для кнопки возврата
    """
    if subcategory_id:
        return f"category_{subcategory_id}"
    elif category_id:
        return CATALOG_CALLBACK
    return CATALOG_CALLBACK


async def safe_callback_execution(
        callback: types.CallbackQuery,
        action: Callable,
        error_message: str = DEFAULT_ERROR_MESSAGE
) -> None:
    """
    Выполняет действие с безопасной обработкой исключений для callback-запросов.

    Args:
        callback: Объект callback_query для взаимодействия с пользователем
        action: Асинхронная функция для выполнения
        error_message: Сообщение об ошибке для пользователя
    """
    try:
        await action()
    except Exception as e:
        user = callback.from_user
        callback_data = callback.data
        error_stack = traceback.format_exc()

        logger.error(
            f"Ошибка при обработке callback '{callback_data}' от пользователя ID:{user.id} ({user.full_name}): "
            f"{e}\n{error_stack}"
        )

        await callback.answer(error_message)
