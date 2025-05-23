import os
import logging
from logging.handlers import RotatingFileHandler

from ..utils.config import LOG_LEVEL, LOG_FILE


def setup_logger():
    """
    Настраивает и возвращает логгер для приложения.

    Создает логгер с настроенным уровнем логирования из конфигурации.
    Настраивает вывод логов в файл с ротацией и в консоль.
    Создает директорию для лог-файла, если она не существует.
    """
    log_level = getattr(logging, LOG_LEVEL, logging.INFO)
    log_file = LOG_FILE

    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger('bot_logger')
    logger.setLevel(log_level)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logger()
