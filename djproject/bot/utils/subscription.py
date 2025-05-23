from typing import List, Dict, Any, Union

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot

from . import logger


async def check_user_subscribed(bot: Bot, user_id: int, chat_id: Union[str, int]) -> bool:
    """
    Проверяет, подписан ли пользователь на указанный канал или группу.

    Функция учитывает различные форматы идентификаторов каналов
    (числовой ID или юзернейм с префиксом '@').
    Также обрабатывает специальные случаи, такие как недоступность списка
    участников для некоторых каналов.

    Args:
        bot: Объект бота для выполнения Telegram API запросов
        user_id: ID пользователя, подписку которого проверяем
        chat_id: ID канала/группы или юзернейм с префиксом '@'

    Returns:
        bool: True, если пользователь подписан, False в противном случае
    """
    try:
        if isinstance(chat_id, str) and chat_id.startswith('@'):
            try:
                chat_info = await bot.get_chat(chat_id)
                chat_id = chat_info.id
            except Exception as e:
                logger.error(f"Ошибка при получении ID канала {chat_id}: {e}")
                return False

        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        error_message = str(e)

        if "member list is inaccessible" in error_message:
            return True

        logger.error(f"Ошибка при проверке подписки пользователя {user_id} на канал {chat_id}: {e}")

        return False


async def get_subscription_status(
        bot: Bot,
        user_id: int,
        channels: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Получает статус подписки пользователя на все указанные каналы/группы.

    Проверяет каждый канал из списка и возвращает список каналов,
    на которые пользователь не подписан.

    Args:
        bot: Объект бота для выполнения запросов к API
        user_id: ID пользователя, подписки которого проверяем
        channels: Список словарей с информацией о каналах. Каждый словарь должен
                 содержать как минимум ключи "chat_id", "name" и "invite_link"

    Returns:
        List[Dict[str, Any]]: Список словарей с информацией о каналах,
                             на которые пользователь не подписан
    """
    not_subscribed: List[Dict[str, Any]] = []

    for channel in channels:
        try:
            is_subscribed = await check_user_subscribed(bot, user_id, channel["chat_id"])
            if not is_subscribed:
                not_subscribed.append(channel)
        except KeyError as e:
            logger.error(f"Ошибка в конфигурации канала: отсутствует ключ {e} | "
                         f"Данные канала: {channel}")
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при проверке подписки пользователя {user_id} "
                         f"на канал {channel.get('name', 'неизвестно')}: {e}")

    return not_subscribed


def get_subscription_markup(not_subscribed_channels: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """
    Создает клавиатуру с кнопками для подписки на непройденные каналы.

    Генерирует клавиатуру с кнопками-ссылками для каждого канала,
    на который пользователю нужно подписаться, и кнопкой для проверки подписки.

    Args:
        not_subscribed_channels: Список словарей с информацией о каналах.
                               Каждый словарь должен содержать ключи
                               "name" и "invite_link"

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками-ссылками для подписки
                             и кнопкой проверки подписки
    """
    try:
        builder = InlineKeyboardBuilder()

        for channel in not_subscribed_channels:
            if "name" not in channel or "invite_link" not in channel:
                logger.error(f"Отсутствуют обязательные ключи для создания кнопки подписки: {channel}")
                continue

            builder.add(InlineKeyboardButton(
                text=f"✅ Подписаться на {channel['name']}",
                url=channel['invite_link']
            ))

        builder.add(InlineKeyboardButton(
            text="🔄 Проверить подписку",
            callback_data="check_subscription"
        ))

        builder.adjust(1)

        return builder.as_markup()
    except Exception as e:
        logger.error(f"Ошибка при создании клавиатуры подписки: {e}")
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(
            text="🔄 Проверить подписку",
            callback_data="check_subscription"
        ))
        return builder.as_markup()
