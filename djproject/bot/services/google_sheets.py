from datetime import datetime
import asyncio

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from ..utils.logger import logger


class GoogleSheetsManager:
    """Класс для работы с Google Sheets"""

    def __init__(self, credentials_file, spreadsheet_id):
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.scope = ['https://spreadsheets.google.com/feeds',
                      'https://www.googleapis.com/auth/drive']
        self.headers = [
            'Дата/время',
            'ID заказа',
            'ID пользователя',
            'Имя',
            'Телефон',
            'Адрес',
            'Сумма',
            'Статус оплаты',
            'Товары'
        ]

    def _get_client(self):
        """Получение авторизованного клиента gspread"""
        try:
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, self.scope)
            return gspread.authorize(credentials)
        except Exception as e:
            logger.error(f"Ошибка при создании клиента Google Sheets: {e}")
            raise

    def _setup_sheet(self, sheet):
        """Проверяет и настраивает заголовки таблицы"""
        try:
            need_resize = False

            if sheet.row_count == 0 or not sheet.row_values(1):
                sheet.append_row(self.headers)
                need_resize = True

                header_range = f"A1:{chr(65 + len(self.headers) - 1)}1"

                yellow_color = {"red": 1.0, "green": 0.9, "blue": 0.4}  # Жёлтый цвет
                sheet.format(header_range, {
                    "backgroundColor": yellow_color,
                    "horizontalAlignment": "CENTER",
                    "textFormat": {"bold": True}
                })

            if need_resize:
                column_widths = [
                    120,
                    80,
                    120,
                    150,
                    120,
                    250,
                    100,
                    120,
                    350
                ]

                requests = []
                for i, width in enumerate(column_widths):
                    requests.append({
                        "updateDimensionProperties": {
                            "range": {
                                "sheetId": 0,
                                "dimension": "COLUMNS",
                                "startIndex": i,
                                "endIndex": i + 1
                            },
                            "properties": {
                                "pixelSize": width
                            },
                            "fields": "pixelSize"
                        }
                    })

                if requests:
                    client = self._get_client()
                    spreadsheet = client.open_by_key(self.spreadsheet_id)
                    spreadsheet.batch_update({"requests": requests})

            return need_resize
        except Exception as e:
            logger.error(f"Ошибка при настройке таблицы Google Sheets: {e}")
            raise

    async def append_order_to_sheet(self, order_data):
        """Асинхронно добавляет данные заказа в Google Таблицу"""

        def _append_order():
            try:
                client = self._get_client()
                sheet = client.open_by_key(self.spreadsheet_id).sheet1

                self._setup_sheet(sheet)

                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                row = [
                    timestamp,
                    order_data['order_id'],
                    order_data['user_id'],
                    order_data['name'],
                    order_data['phone'],
                    order_data['address'],
                    order_data['total_amount'],
                    order_data['payment_status'],
                    order_data['products']
                ]

                sheet.append_row(row)

                return True
            except KeyError as e:
                logger.error(f"Ошибка в данных заказа при добавлении в Google Sheets: отсутствует ключ {e} | "
                             f"Данные заказа: {order_data}")
                return False
            except gspread.exceptions.APIError as e:
                logger.error(f"Ошибка API Google Sheets: {e}")
                return False
            except Exception as e:
                logger.error(f"Ошибка при добавлении заказа в Google Sheets: {e} | "
                             f"ID заказа: {order_data.get('order_id', 'неизвестно')}, "
                             f"ID пользователя: {order_data.get('user_id', 'неизвестно')}")
                return False

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _append_order)
        except Exception as e:
            logger.error(f"Ошибка при выполнении асинхронной операции с Google Sheets: {e}")
            return False
