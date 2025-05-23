import asyncio
import sys
import traceback

from aiogram import Bot, Dispatcher

from .handlers.faq import faq_router
from .handlers.common import common_router
from .handlers.catalog import catalog_router
from .handlers.main_menu import main_menu_router
from .utils.config import BOT_TOKEN
from .utils.logger import logger


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(faq_router)
dp.include_router(catalog_router)
dp.include_router(common_router)
dp.include_router(main_menu_router)


async def main():
    try:
        bot_info = await bot.get_me()
        logger.info(f"БОТ ЗАПУЩЕН: {bot_info.full_name} (@{bot_info.username})")

        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        logger.info("БОТ ОСТАНОВЛЕН")
    except Exception as e:
        error_info = f"Критическая ошибка при запуске бота: {e}\n{traceback.format_exc()}"
        logger.error(error_info)
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        error_info = f"Ошибка в основном блоке запуска: {e}\n{traceback.format_exc()}"
        logger.error(error_info)
