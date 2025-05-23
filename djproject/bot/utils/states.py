from aiogram.fsm.state import State, StatesGroup


class FAQStates(StatesGroup):
    waiting_for_question = State()


class CatalogStates(StatesGroup):
    waiting_for_quantity = State()
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_address = State()
