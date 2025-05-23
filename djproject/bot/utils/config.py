import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv


load_dotenv()


MAIN_MENU_CALLBACK = "main_menu"
FAQ_CALLBACK = "faq"
FAQ_LIST_CALLBACK = "faq_list"
BACK_TO_FAQ_CALLBACK = "back_to_faq"
ASK_QUESTION_CALLBACK = "ask_question"
USER_QUESTION_PREFIX = "uq_"
CART_CALLBACK = "cart"
CATALOG_CALLBACK = "catalog"
QUANTITY_CALLBACK_PREFIX = "quantity_"
ADD_TO_CART_PREFIX = "add_to_cart_"
REMOVE_PREFIX = "remove_"
CLEAR_CART_CALLBACK = "clear_cart"

PRODUCTS_PER_PAGE = 5
MAX_PRODUCT_QUANTITY = 100
SUCCESS_MESSAGE = "{product} (x{quantity}) добавлен в корзину!"
QUANTITY_ERROR = "Пожалуйста, введите число от 1 до {max_quantity}."
DEFAULT_ERROR_MESSAGE = "Произошла ошибка. Пожалуйста, попробуйте позже."
CART_EMPTY_MESSAGE = "Ваша корзина пуста."

# Настройки бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Настройка логов
LOG_LEVEL = os.getenv('LOG_LEVEL')
LOG_FILE = os.getenv('LOG_FILE')

# Настройки платежных систем
TINKOFF_TERMINAL_KEY = os.getenv("TINKOFF_TERMINAL_KEY", "TinkoffBankTest")
TINKOFF_PASSWORD = os.getenv("TINKOFF_PASSWORD", "TinkoffBankTest")
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "123456")
YOOKASSA_API_KEY = os.getenv("YOOKASSA_API_KEY", "test_api_key")

# Настройки Google Sheets
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
GOOGLE_SHEETS_SPREADSHEET_ID = os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID")

REQUIRED_CHANNELS = [
    {
        "chat_id": "@username",  # Замените на username вашего канала
        "name": "Канал для теста бота",
        "invite_link": "https://t.me/username"
    },
    {
        "chat_id": "@username",  # Замените на username вашей группы
        "name": "Канал для теста группы",
        "invite_link": "https://t.me/username"
    }
]
