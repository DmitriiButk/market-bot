from asgiref.sync import sync_to_async

from .setup import *
from core.models import Order, OrderItem

from ..services.google_sheets import GoogleSheetsManager
from ..utils.config import GOOGLE_SHEETS_CREDENTIALS_FILE, GOOGLE_SHEETS_SPREADSHEET_ID


async def save_order_to_google_sheets(order_id: int) -> bool:
    """
    Сохраняет данные заказа в Google таблицу.

    Получает детальную информацию о заказе, его товарах и отправляет
    эти данные в Google Sheets через специализированный менеджер.

    Args:
        order_id: Идентификатор заказа для сохранения

    Returns:
        True, если данные успешно сохранены, иначе False
    """
    try:
        order = await sync_to_async(Order.objects.select_related().get)(id=order_id)

        order_items = await sync_to_async(list)(OrderItem.objects.filter(order_id=order_id))

        products_text = ""
        for item in order_items:
            product_name = await sync_to_async(lambda: item.product.name)()
            price = item.price
            quantity = item.quantity
            products_text += f"{product_name} x {quantity} = {price * quantity} ₽\n"

        order_data = {
            'order_id': order.id,
            'user_id': order.user_id,
            'name': order.name,
            'phone': order.phone,
            'address': order.address,
            'total_amount': float(order.total_amount),
            'payment_status': order.payment_status,
            'products': products_text
        }

        sheets_manager = GoogleSheetsManager(
            GOOGLE_SHEETS_CREDENTIALS_FILE,
            GOOGLE_SHEETS_SPREADSHEET_ID
        )

        result = await sheets_manager.append_order_to_sheet(order_data)
        return result

    except Exception as e:
        print(f"Ошибка при сохранении заказа в Google Sheets: {e}")
        return False
