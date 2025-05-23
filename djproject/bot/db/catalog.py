from typing import List, Dict, Any, Tuple, Optional
from asgiref.sync import sync_to_async

from .setup import *
from core.models import Product, ProductCategory, ProductSubcategory


@sync_to_async
def get_product_categories() -> List[Dict[str, Any]]:
    """
    Получает список активных категорий товаров.

    Returns:
        Список словарей с информацией о категориях (id и название),
        отсортированный по порядку и имени
    """
    categories = ProductCategory.objects.filter(active=True).order_by('order', 'name')
    return [{'id': cat.id, 'name': cat.name} for cat in categories]


@sync_to_async
def get_subcategories(category_id: int) -> List[Dict[str, Any]]:
    """
    Получает подкатегории для указанной категории.

    Args:
        category_id: Идентификатор родительской категории

    Returns:
        Список словарей с информацией о подкатегориях (id и название),
        отсортированный по порядку и имени
    """
    subcats = ProductSubcategory.objects.filter(
        category_id=category_id,
        active=True
    ).order_by('order', 'name')
    return [{'id': sub.id, 'name': sub.name} for sub in subcats]


@sync_to_async
def get_category_name(category_id: int) -> str:
    """
    Получает название категории по ID.

    Args:
        category_id: Идентификатор категории

    Returns:
        Название категории или строка "Категория", если категория не найдена
    """
    category = ProductCategory.objects.filter(id=category_id).first()
    return category.name if category else "Категория"


@sync_to_async
def get_subcategory_name(subcategory_id: int) -> str:
    """
    Получает название подкатегории по ID.

    Args:
        subcategory_id: Идентификатор подкатегории

    Returns:
        Название подкатегории или строка "Подкатегория", если подкатегория не найдена
    """
    subcategory = ProductSubcategory.objects.filter(id=subcategory_id).first()
    return subcategory.name if subcategory else "Подкатегория"


@sync_to_async
def get_parent_category(subcategory_id: int) -> Optional[int]:
    """
    Получает ID родительской категории для подкатегории.

    Args:
        subcategory_id: Идентификатор подкатегории

    Returns:
        ID родительской категории или None, если подкатегория не найдена
    """
    subcategory = ProductSubcategory.objects.filter(id=subcategory_id).first()
    return subcategory.category_id if subcategory else None


@sync_to_async
def get_products(
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 10
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Получает список товаров с пагинацией и фильтрацией по категории/подкатегории.

    Args:
        category_id: ID категории для фильтрации (опционально)
        subcategory_id: ID подкатегории для фильтрации (опционально)
        page: Номер страницы для пагинации (начиная с 1)
        per_page: Количество товаров на одной странице

    Returns:
        Кортеж из двух элементов:
        - Список товаров в виде словарей с информацией о каждом товаре
        - Общее количество товаров, соответствующих условиям фильтрации
    """
    products_query = Product.objects.filter(active=True)

    if category_id:
        products_query = products_query.filter(category_id=category_id)

    if subcategory_id:
        products_query = products_query.filter(subcategory_id=subcategory_id)

    total_count = products_query.count()

    start = (page - 1) * per_page
    end = start + per_page
    products = products_query.order_by('order', 'name')[start:end]

    result = []
    for p in products:
        product_dict = {
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': p.price,
            'category_id': p.category_id,
            'subcategory_id': p.subcategory_id
        }

        if p.image:
            product_dict['image'] = p.image.url
        else:
            product_dict['image'] = None

        result.append(product_dict)

    return result, total_count


@sync_to_async
def get_product(product_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает детальную информацию о товаре по ID.

    Args:
        product_id: Идентификатор товара

    Returns:
        Словарь с информацией о товаре или None, если товар не найден или неактивен
    """
    product = Product.objects.filter(id=product_id, active=True).first()

    if not product:
        return None

    result = {
        'id': product.id,
        'name': product.name,
        'description': product.description,
        'price': product.price,
        'category_id': product.category_id,
        'subcategory_id': product.subcategory_id
    }

    if product.image:
        result['image'] = product.image.url
    else:
        result['image'] = None

    return result