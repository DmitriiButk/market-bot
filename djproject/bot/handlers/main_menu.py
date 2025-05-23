from typing import List, Dict, Any

from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .. import db


main_menu_router = Router()


def get_main_menu_kb() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру главного меню.

    Клавиатура содержит кнопки для перехода к каталогу товаров,
    корзине и часто задаваемым вопросам.

    Returns:
        InlineKeyboardMarkup: Клавиатура главного меню
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛍️ Каталог товаров", callback_data="catalog")],
            [InlineKeyboardButton(text="🛒 Корзина", callback_data="cart")],
            [InlineKeyboardButton(text="❓ FAQ", callback_data="faq")]
        ]
    )


def get_main_menu_button_kb() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с единственной кнопкой возврата в главное меню.

    Используется в различных разделах для предоставления пользователю
    возможности вернуться на главную страницу бота.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой возврата в главное меню
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
        ]
    )


@main_menu_router.callback_query(lambda c: c.data == "main_menu")
async def main_menu(callback: types.CallbackQuery) -> None:
    """
    Обработчик callback-запроса для отображения главного меню.

    Редактирует текущее сообщение, заменяя его на приветствие
    с клавиатурой главного меню.

    Args:
        callback: Объект callback_query от нажатия на кнопку возврата в главное меню
    """
    await callback.message.edit_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=get_main_menu_kb()
    )
    await callback.answer()


@main_menu_router.callback_query(lambda c: c.data == "faq")
async def show_faq(callback: types.CallbackQuery) -> None:
    """
    Обработчик callback-запроса для отображения списка часто задаваемых вопросов.

    Получает список FAQ из базы данных и формирует интерактивное меню
    с вопросами, на которые можно нажать для просмотра ответов.

    Args:
        callback: Объект callback_query от нажатия на кнопку FAQ
    """
    faqs: List[Dict[str, Any]] = await db.get_faq()

    if not faqs:
        await callback.message.edit_text(
            "В базе данных пока нет вопросов и ответов.",
            reply_markup=get_main_menu_button_kb()
        )
        await callback.answer()
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=faq['question'], callback_data=f"faq_{faq['id']}")]
                            for faq in faqs
                        ] + [
                            [InlineKeyboardButton(text="Задать свой вопрос", callback_data="ask_question")],
                            [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="main_menu")]
                        ]
    )

    await callback.message.edit_text("Часто задаваемые вопросы:", reply_markup=kb)
    await callback.answer()


@main_menu_router.message(F.text == "FAQ")
async def menu_faq(message: types.Message) -> None:
    """
    Обработчик текстовой команды "FAQ" для отображения часто задаваемых вопросов.

    Получает список FAQ из базы данных и формирует интерактивное меню с вопросами.
    Если в базе нет вопросов, уведомляет пользователя об этом.

    Args:
        message: Объект сообщения от пользователя
    """
    faqs: List[Dict[str, Any]] = await db.get_faq()

    if not faqs:
        await message.answer(
            "В базе данных пока нет вопросов и ответов.",
            reply_markup=get_main_menu_button_kb()
        )
        return

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
                            [InlineKeyboardButton(text=faq['question'], callback_data=f"faq_{faq['id']}")]
                            for faq in faqs
                        ] + [
                            [InlineKeyboardButton(text="Задать свой вопрос", callback_data="ask_question")],
                            [InlineKeyboardButton(text="🏠 Вернуться в меню", callback_data="main_menu")]
                        ]
    )

    await message.answer("Часто задаваемые вопросы:", reply_markup=kb)
