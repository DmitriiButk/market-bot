from typing import List, Dict, Any
from asgiref.sync import sync_to_async
from django.db import transaction

from .setup import *
from core.models import Order, OrderItem, Product


@sync_to_async
def create_order(
        user_id: int,
        items: List[Dict[str, Any]],
        name: str,
        phone: str,
        address: str,
        total_amount: float
) -> int:
    """
    Создает заказ в базе данных.

    Создает запись заказа и связанные с ним элементы заказа.
    Использует транзакцию для обеспечения атомарности операции.

    Args:
        user_id: Идентификатор пользователя
        items: Список товаров в заказе (словари с данными о товарах)
        name: Имя заказчика
        phone: Телефон заказчика
        address: Адрес доставки
        total_amount: Общая сумма заказа

    Returns:
        ID созданного заказа
    """
    with transaction.atomic():
        # Создаем заказ
        order = Order.objects.create(
            user_id=user_id,
            name=name,
            phone=phone,
            address=address,
            total_amount=total_amount
        )

        # Добавляем товары в заказ
        for item in items:
            product = Product.objects.get(id=item['product_id'])
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=item['quantity'],
                price=item['price']
            )

        return order.id


@sync_to_async
def update_order_payment_info(
        order_id: int,
        payment_id: str,
        payment_url: str,
        payment_status: str = "pending"
) -> bool:
    """
    Обновляет информацию о платеже для заказа.

    Args:
        order_id: Идентификатор заказа
        payment_id: Идентификатор платежа в платежной системе
        payment_url: URL для перехода к форме оплаты
        payment_status: Статус платежа (по умолчанию "pending")

    Returns:
        True, если информация успешно обновлена, иначе False
    """
    try:
        order = Order.objects.get(id=order_id)

        # Обновляем поля платежа
        order.payment_id = payment_id
        order.payment_url = payment_url
        order.payment_status = payment_status
        order.save()

        return True
    except Order.DoesNotExist:
        print(f"Заказ с ID {order_id} не найден")
        return False
    except Exception as e:
        print(f"Ошибка при обновлении информации о платеже: {e}")
        return False