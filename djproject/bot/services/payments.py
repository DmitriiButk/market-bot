import uuid
from typing import Dict, Any, Optional, Union

from aiohttp import BasicAuth, ClientSession

from ..utils.logger import logger


class TinkoffPayment:
    """
    Класс для работы с платежным API Тинькофф (тестовый режим).

    Позволяет создавать платежи и получать информацию через API Тинькофф Банка.
    Реализует асинхронное взаимодействие с API.

    Attributes:
        terminal_key: Идентификатор терминала продавца
        password: Секретный ключ терминала
        base_url: Базовый URL API Тинькофф
    """

    def __init__(self, terminal_key: str, password: str) -> None:
        """
        Инициализирует клиент API Тинькофф с указанными учетными данными.

        Args:
            terminal_key: Идентификатор терминала в системе Тинькофф
            password: Секретный ключ для авторизации запросов
        """
        self.terminal_key: str = terminal_key
        self.password: str = password
        self.base_url: str = "https://securepay.tinkoff.ru/v2/"

    async def create_payment(
            self,
            order_id: str,
            amount: Union[int, float],
            description: str,
            customer_email: Optional[str] = None,
            customer_phone: Optional[str] = None,
            success_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создает новый платеж в системе Тинькофф.

        Формирует и отправляет запрос к API для инициализации платежа.
        Возвращает ответ от API с данными созданного платежа или информацией об ошибке.

        Args:
            order_id: Уникальный идентификатор заказа в вашей системе
            amount: Сумма платежа в рублях (будет преобразована в копейки)
            description: Описание заказа для отображения пользователю
            customer_email: Email клиента для отправки чека (опционально)
            customer_phone: Телефон клиента для уведомлений (опционально)
            success_url: URL для перенаправления после успешной оплаты

        Returns:
            Dict[str, Any]: Ответ от API со статусом операции и данными платежа
                           (включая ссылку на форму оплаты в случае успеха)

        Raises:
            Exception: При возникновении ошибок сетевого соединения или API
        """
        payload: Dict[str, Any] = {
            "TerminalKey": self.terminal_key,
            "Amount": int(amount * 100),
            "OrderId": order_id,
            "Description": description,
        }

        if customer_email or customer_phone:
            payload["DATA"] = {}
            if customer_phone:
                payload["DATA"]["Phone"] = customer_phone
            if customer_email:
                payload["DATA"]["Email"] = customer_email

        if success_url:
            payload["SuccessURL"] = success_url

        try:
            async with ClientSession() as session:
                async with session.post(f"{self.base_url}Init", json=payload) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Ошибка при создании платежа в Тинькофф: {e} | "
                         f"OrderId: {order_id}, Amount: {amount}, Description: {description}")
            return {"Success": False, "Message": str(e)}


class YookassaPayment:
    """
    Класс для работы с платежным API ЮKassa (тестовый режим).

    Позволяет создавать платежи через API ЮKassa с использованием
    базовой аутентификации и асинхронных запросов.

    Attributes:
        shop_id: Идентификатор магазина в системе ЮKassa
        api_key: Секретный ключ для API запросов
        base_url: Базовый URL API ЮKassa
    """

    def __init__(self, shop_id: str, api_key: str) -> None:
        """
        Инициализирует клиент API ЮKassa с указанными учетными данными.

        Args:
            shop_id: Идентификатор магазина в системе ЮKassa
            api_key: Секретный ключ для авторизации запросов
        """
        self.shop_id: str = shop_id
        self.api_key: str = api_key
        self.base_url: str = "https://api.yookassa.ru/v3/payments"

    async def create_payment(
            self,
            amount: Union[int, float],
            description: str,
            return_url: Optional[str] = None,
            customer_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Создает новый платеж в системе ЮKassa.

        Формирует и отправляет запрос к API ЮKassa для создания платежа.
        Поддерживает перенаправление пользователя на страницу оплаты и
        добавление информации о клиенте для формирования чека.

        Args:
            amount: Сумма платежа в рублях
            description: Описание заказа (отображается клиенту и используется в чеке)
            return_url: URL для перенаправления клиента после оплаты
            customer_email: Email клиента для отправки чека

        Returns:
            Dict[str, Any]: Ответ от API со статусом операции и данными платежа
                           (включая идентификатор платежа и ссылку на форму оплаты)

        Raises:
            Exception: При возникновении ошибок сетевого соединения или API
        """
        headers: Dict[str, str] = {
            "Idempotence-Key": str(uuid.uuid4()),
            "Content-Type": "application/json"
        }

        auth: BasicAuth = BasicAuth(login=self.shop_id, password=self.api_key)

        payload: Dict[str, Any] = {
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "description": description
        }

        if customer_email:
            payload["receipt"] = {
                "customer": {
                    "email": customer_email
                },
                "items": [
                    {
                        "description": description,
                        "quantity": "1",
                        "amount": {
                            "value": str(amount),
                            "currency": "RUB"
                        },
                        "vat_code": "1"  # НДС 20%
                    }
                ]
            }

        try:
            async with ClientSession() as session:
                async with session.post(
                        self.base_url,
                        json=payload,
                        auth=auth,
                        headers=headers
                ) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Ошибка при создании платежа в ЮKassa: {e} | "
                         f"Amount: {amount}, Description: {description}, "
                         f"Email: {customer_email if customer_email else 'не указан'}")
            return {"success": False, "message": str(e)}
