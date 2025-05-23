from typing import List, Dict, Any

from aiogram import types, Router
from aiogram.filters import CommandStart

from ..utils.subscription import get_subscription_status, get_subscription_markup
from ..utils.config import REQUIRED_CHANNELS
from ..handlers.main_menu import get_main_menu_kb
from ..utils.logger import logger


common_router = Router()


@common_router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    """
    Обработчик команды /start с проверкой подписки.

    Проверяет подписку пользователя на обязательные каналы.
    Если пользователь не подписан на все каналы, предлагает подписаться.
    В противном случае показывает главное меню.

    Args:
        message: Объект сообщения от пользователя с командой /start
    """
    try:
        user_id: int = message.from_user.id

        not_subscribed: List[Dict[str, Any]] = await get_subscription_status(
            message.bot, user_id, REQUIRED_CHANNELS
        )

        if not_subscribed:
            await show_subscription_request(message, not_subscribed)
        else:
            await show_main_menu(message)
    except Exception as e:
        user = message.from_user
        logger.error(f"Ошибка при обработке команды /start от пользователя {user.full_name} [ID:{user.id}]: {e}")
        await message.answer("Произошла ошибка при обработке запроса. Попробуйте позже.")


@common_router.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery) -> None:
    """
    Обработчик проверки подписки после нажатия кнопки "Проверить подписку".

    Повторно проверяет подписки пользователя на требуемые каналы.
    Если пользователь полностью подписан, показывает главное меню.
    Иначе обновляет сообщение с требованием подписаться.

    Args:
        callback: Объект callback_query от нажатия на кнопку проверки подписки
    """
    try:
        user_id: int = callback.from_user.id

        not_subscribed: List[Dict[str, Any]] = await get_subscription_status(
            callback.bot, user_id, REQUIRED_CHANNELS
        )

        if not_subscribed:
            await handle_incomplete_subscription(callback, not_subscribed)
        else:
            await callback.answer("Спасибо за подписку! Теперь вам доступен полный функционал бота.")
            await callback.message.delete()  # Удаляем сообщение о подписке
            await show_main_menu(callback.message)
    except Exception as e:
        user = callback.from_user
        logger.error(f"Ошибка при проверке подписки пользователя {user.full_name} [ID:{user.id}]: {e}")
        await callback.answer("Произошла ошибка. Попробуйте позже.", show_alert=True)


async def show_main_menu(message: types.Message) -> None:
    """
    Показывает главное меню бота.

    Отправляет приветственное сообщение с клавиатурой главного меню,
    содержащей кнопки для навигации по различным разделам бота.

    Args:
        message: Объект сообщения, используемый для отправки ответа
    """
    try:
        await message.answer(
            f"👋 Добро пожаловать, {message.from_user.first_name}!\n\n"
            f"Выберите раздел, который вас интересует:",
            reply_markup=get_main_menu_kb()
        )
    except Exception as e:
        logger.error(f"Ошибка при отображении главного меню: {e}")
        raise


async def show_subscription_request(message: types.Message,
                                    not_subscribed: List[Dict[str, Any]]) -> None:
    """
    Показывает пользователю запрос на подписку на требуемые каналы.

    Формирует сообщение со списком каналов, на которые нужно подписаться,
    и кнопкой для проверки подписки.

    Args:
        message: Объект сообщения для отправки ответа
        not_subscribed: Список каналов, на которые пользователь не подписан
    """
    try:
        channels_text: str = "\n".join([f"• {channel['name']}" for channel in not_subscribed])

        await message.answer(
            f"👋 Привет, {message.from_user.first_name}!\n\n"
            f"Для использования бота, пожалуйста, подпишитесь на:\n"
            f"{channels_text}\n\n"
            f"После подписки нажмите кнопку «Проверить подписку»",
            reply_markup=get_subscription_markup(not_subscribed)
        )
    except Exception as e:
        logger.error(f"Ошибка при отображении запроса на подписку: {e}")
        raise


async def handle_incomplete_subscription(callback: types.CallbackQuery,
                                         not_subscribed: List[Dict[str, Any]]) -> None:
    """
    Обрабатывает ситуацию, когда пользователь проверил подписку,
    но подписан не на все каналы.

    Обновляет сообщение со списком непройденных подписок или
    показывает всплывающее уведомление, если список не изменился.

    Args:
        callback: Объект callback_query для взаимодействия с пользователем
        not_subscribed: Список каналов, на которые пользователь не подписан
    """
    try:
        channels_text: str = "\n".join([f"• {channel['name']}" for channel in not_subscribed])
        await callback.answer("Вы подписались не на все каналы!")

        new_text: str = (f"Для использования бота, пожалуйста, подпишитесь на:\n"
                         f"{channels_text}\n\n"
                         f"После подписки нажмите кнопку «Проверить подписку»")

        if callback.message.text != new_text:
            await callback.message.edit_text(
                new_text,
                reply_markup=get_subscription_markup(not_subscribed)
            )
        else:
            await callback.answer("Подпишитесь на все указанные каналы", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при обработке неполной подписки: {e}")
        raise
