from typing import List, Dict, Any
from asgiref.sync import sync_to_async

from .setup import *
from core.models import CartItem


@sync_to_async
def add_item_to_cart(user_id: int, product_id: int, quantity: int = 1) -> bool:
    """
    Добавляет товар в корзину пользователя.

    Если товар уже есть в корзине, увеличивает его количество.
    Если товара нет в корзине, создает новую запись.

    Args:
        user_id: Идентификатор пользователя
        product_id: Идентификатор товара
        quantity: Количество добавляемого товара

    Returns:
        True в случае успешного добавления
    """
    cart_item = CartItem.objects.filter(user_id=user_id, product_id=product_id).first()

    if cart_item:
        cart_item.quantity += quantity
        cart_item.save()
    else:
        CartItem.objects.create(
            user_id=user_id,
            product_id=product_id,
            quantity=quantity
        )
    return True


@sync_to_async
def get_cart_items(user_id: int) -> List[Dict[str, Any]]:
    """
    Получает список товаров в корзине пользователя.

    Args:
        user_id: Идентификатор пользователя

    Returns:
        Список словарей с информацией о товарах в корзине
    """
    items = CartItem.objects.filter(user_id=user_id).select_related('product')

    result = []
    for item in items:
        item_dict = {
            'id': item.id,
            'product_id': item.product.id,
            'name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity
        }

        if item.product.image:
            item_dict['image'] = item.product.image.url
        else:
            item_dict['image'] = None

        result.append(item_dict)

    return result


@sync_to_async
def remove_item_from_cart(user_id: int, cart_item_id: int) -> bool:
    """
    Удаляет товар из корзины.

    Args:
        user_id: Идентификатор пользователя
        cart_item_id: Идентификатор элемента корзины

    Returns:
        True в случае успешного удаления
    """
    CartItem.objects.filter(id=cart_item_id, user_id=user_id).delete()
    return True


@sync_to_async
def clear_user_cart(user_id: int) -> bool:
    """
    Очищает всю корзину пользователя.

    Args:
        user_id: Идентификатор пользователя

    Returns:
        True в случае успешной очистки корзины
    """
    CartItem.objects.filter(user_id=user_id).delete()
    return True