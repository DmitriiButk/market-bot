from typing import List, Dict, Any, Tuple, Optional
from asgiref.sync import sync_to_async

from .setup import *
from core.models import UserQuestion


@sync_to_async
def add_user_question(user_id: int, question: str) -> None:
    """
    Добавляет новый вопрос пользователя в базу данных.

    Args:
        user_id: Идентификатор пользователя, задавшего вопрос
        question: Текст вопроса
    """
    UserQuestion.objects.create(user_id=user_id, question=question)


@sync_to_async
def get_user_questions(answered: Optional[bool] = None) -> List[Dict[str, Any]]:
    """
    Получает список вопросов пользователей с возможностью фильтрации по статусу.

    Args:
        answered: Если указано, фильтрует вопросы по статусу ответа
                 (True - отвеченные, False - неотвеченные, None - все)

    Returns:
        Список словарей с информацией о вопросах пользователей
    """
    qs = UserQuestion.objects.all()
    if answered is not None:
        qs = qs.filter(is_answered=answered)

    return [
        {
            "id": q.id,
            "user_id": q.user_id,
            "question": q.question,
            "answer": q.answer,
            "is_answered": q.is_answered,
            "created_at": q.created_at
        }
        for q in qs.order_by("-created_at")
    ]


@sync_to_async
def save_answer(question_id: int, answer_text: str) -> Tuple[bool, Optional[int]]:
    """
    Сохраняет ответ на вопрос пользователя.

    Args:
        question_id: Идентификатор вопроса
        answer_text: Текст ответа

    Returns:
        Кортеж (успех_операции, id_пользователя):
        - Первый элемент: True, если ответ успешно сохранен, иначе False
        - Второй элемент: ID пользователя, если вопрос найден, иначе None
    """
    try:
        question = UserQuestion.objects.get(id=question_id)
        question.answer = answer_text
        question.is_answered = True
        question.save()
        return True, question.user_id
    except UserQuestion.DoesNotExist:
        return False, None


@sync_to_async
def get_answered_user_questions() -> List[Dict[str, Any]]:
    """
    Получает отвеченные вопросы пользователей для раздела FAQ.

    Returns:
        Список словарей с информацией об отвеченных вопросах,
        содержащих id, вопрос и ответ
    """
    qs = UserQuestion.objects.filter(is_answered=True).order_by("-created_at")
    return [
        {
            "id": q.id,
            "question": q.question,
            "answer": q.answer
        }
        for q in qs
    ]