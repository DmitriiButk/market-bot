from typing import Dict, Any, List, Optional

from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from .. import db
from ..utils.config import MAIN_MENU_CALLBACK, FAQ_LIST_CALLBACK, ASK_QUESTION_CALLBACK, USER_QUESTION_PREFIX, \
    FAQ_CALLBACK, BACK_TO_FAQ_CALLBACK
from ..utils.states import FAQStates
from ..utils.logger import logger


faq_router = Router()


def get_main_menu_button() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с единственной кнопкой возврата в главное меню.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопкой главного меню
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU_CALLBACK)]
        ]
    )


async def get_faq_list_keyboard() -> InlineKeyboardMarkup:
    """
    Создает клавиатуру выбора действий в разделе FAQ.

    Клавиатура содержит кнопки для просмотра списка вопросов,
    возможности задать свой вопрос и вернуться в главное меню.

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками действий в разделе FAQ
    """
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список вопросов", callback_data=FAQ_LIST_CALLBACK)],
            [InlineKeyboardButton(text="✍️ Задать свой вопрос", callback_data=ASK_QUESTION_CALLBACK)],
            [InlineKeyboardButton(text="🔙 Вернуться в меню", callback_data=MAIN_MENU_CALLBACK)]
        ]
    )


@faq_router.callback_query(lambda c: c.data == FAQ_LIST_CALLBACK)
async def show_faq_list(callback: types.CallbackQuery) -> None:
    """
    Обработчик для отображения списка отвеченных пользовательских вопросов.

    Получает из базы данных все отвеченные вопросы и отображает их список
    с возможностью выбора конкретного вопроса для просмотра ответа.

    Args:
        callback: Объект callback_query с данными о пользователе и сообщении
    """
    try:
        user_questions: List[Dict[str, Any]] = await db.get_answered_user_questions()

        if not user_questions:
            await callback.message.edit_text(
                "В базе данных пока нет отвеченных вопросов.",
                reply_markup=await get_faq_list_keyboard()
            )
            return

        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                                [InlineKeyboardButton(
                                    text=q['question'][:50] + ('...' if len(q['question']) > 50 else ''),
                                    callback_data=f"{USER_QUESTION_PREFIX}{q['id']}"
                                )] for q in user_questions
                            ] + [
                                [InlineKeyboardButton(text="◀️ Назад", callback_data=FAQ_CALLBACK)]
                            ]
        )

        await callback.message.edit_text("Выберите вопрос из списка:", reply_markup=kb)


    except Exception as e:
        if "message is not modified" in str(e):
            await callback.answer("Вы уже смотрите список вопросов")
        else:
            logger.error(f"Ошибка при загрузке списка вопросов для пользователя ID:{callback.from_user.id}: {e}")
            await callback.answer("Произошла ошибка при загрузке списка вопросов")

    await callback.answer()


@faq_router.callback_query(lambda c: c.data == FAQ_CALLBACK)
async def show_faq(callback: types.CallbackQuery) -> None:
    """
    Обработчик для отображения главной страницы раздела FAQ.

    Отображает основной экран раздела FAQ с возможностью
    перейти к списку вопросов или задать свой вопрос.

    Args:
        callback: Объект callback_query с данными о пользователе и сообщении
    """
    kb: InlineKeyboardMarkup = await get_faq_list_keyboard()
    await callback.message.edit_text("Раздел FAQ. Выберите действие:", reply_markup=kb)
    await callback.answer()


@faq_router.callback_query(lambda c: c.data == BACK_TO_FAQ_CALLBACK)
async def back_to_faq(callback: types.CallbackQuery) -> None:
    """
    Обработчик для возврата к главной странице раздела FAQ.

    Используется для возврата после просмотра конкретного вопроса и ответа.

    Args:
        callback: Объект callback_query с данными о пользователе и сообщении
    """
    kb: InlineKeyboardMarkup = await get_faq_list_keyboard()
    await callback.message.edit_text("Часто задаваемые вопросы:", reply_markup=kb)
    await callback.answer()


@faq_router.callback_query(lambda c: c.data.startswith(USER_QUESTION_PREFIX))
async def answer_faq(callback: types.CallbackQuery) -> None:
    """
    Обработчик для отображения конкретного вопроса и ответа.

    Извлекает ID вопроса из callback_data, находит соответствующий вопрос
    в базе данных и отображает вопрос вместе с ответом.

    Args:
        callback: Объект callback_query с данными в формате "uq_{id вопроса}"
    """
    try:
        uq_id: int = int(callback.data.split("_")[1])
        user_questions: List[Dict[str, Any]] = await db.get_answered_user_questions()

        question: Optional[Dict[str, Any]] = next(
            (q for q in user_questions if q['id'] == uq_id), None
        )

        if question and question['answer']:
            back_kb: InlineKeyboardMarkup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад к вопросам", callback_data=BACK_TO_FAQ_CALLBACK)],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU_CALLBACK)]
                ]
            )

            await callback.message.edit_text(
                f"<b>Вопрос:</b> {question['question']}\n\n<b>Ответ:</b> {question['answer']}",
                reply_markup=back_kb,
                parse_mode="HTML"
            )
        else:
            await callback.answer("Вопрос не найден или на него еще нет ответа")


    except Exception as e:
        logger.error(f"Ошибка при отображении вопроса ID:{uq_id if 'uq_id' in locals() else 'неизвестно'} "
                     f"для пользователя ID:{callback.from_user.id}: {e}")
        await callback.answer("Произошла ошибка при загрузке вопроса")

    await callback.answer()


@faq_router.callback_query(lambda c: c.data == ASK_QUESTION_CALLBACK)
async def ask_question(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик для инициирования процесса задания пользовательского вопроса.

    Устанавливает состояние ожидания вопроса и просит пользователя
    ввести свой вопрос в текстовом сообщении.

    Args:
        callback: Объект callback_query от нажатия на кнопку "Задать свой вопрос"
        state: Объект для работы с состояниями конечного автомата
    """
    await callback.message.edit_text(
        "Пожалуйста, напишите свой вопрос в следующем сообщении:"
    )
    await state.set_state(FAQStates.waiting_for_question)
    await callback.answer()


@faq_router.message(FAQStates.waiting_for_question)
async def save_user_question(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик для сохранения пользовательского вопроса.

    Сохраняет введенный пользователем вопрос в базу данных и
    отображает сообщение с подтверждением.

    Args:
        message: Объект сообщения с текстом вопроса
        state: Объект для работы с состояниями конечного автомата
    """
    try:
        await db.add_user_question(message.from_user.id, message.text)

        back_kb: InlineKeyboardMarkup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Вернуться в FAQ", callback_data=FAQ_CALLBACK)],
                [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MAIN_MENU_CALLBACK)]
            ]
        )

        await message.answer(
            "Спасибо! Ваш вопрос отправлен администрации. "
            "Мы рассмотрим его и опубликуем ответ в ближайшее время.",
            reply_markup=back_kb
        )

    except Exception as e:
        logger.error(f"Ошибка при сохранении вопроса от пользователя ID:{message.from_user.id}: {e}")
        await message.answer("Произошла ошибка при сохранении вашего вопроса. Пожалуйста, попробуйте позже.")

    await state.clear()
