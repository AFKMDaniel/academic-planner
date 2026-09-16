from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import LESSON_TYPES, CurriculumSubject, Lesson
from app.services.curriculum_subject_service import allocated_lesson_hours


class LessonError(Exception):
    """Raised when a lesson operation violates a validation rule."""


def list_lessons(session: Session, curriculum_subject_id: int) -> list[Lesson]:
    return list(
        session.scalars(
            select(Lesson)
            .where(Lesson.curriculum_subject_id == curriculum_subject_id)
            .order_by(Lesson.lesson_number, Lesson.id)
        )
    )


def add_lesson(
    session: Session,
    curriculum_subject_id: int | None,
    lesson_number: int | str,
    lesson_date: date | None,
    topic: str,
    hours: int | str,
    lesson_type: str | None,
    notes: str | None = None,
) -> Lesson:
    curriculum_subject = (
        session.get(CurriculumSubject, curriculum_subject_id)
        if curriculum_subject_id is not None
        else None
    )
    if curriculum_subject is None:
        raise LessonError("Выберите предмет учебного плана для занятия.")

    number = _validate_positive_int(lesson_number, "Номер занятия")
    lesson_hours = _validate_positive_int(hours, "Часы")
    _validate_date(lesson_date)
    clean_topic = _validate_topic(topic)
    _validate_lesson_type(lesson_type)
    _validate_allocated_hours(session, curriculum_subject, lesson_hours)

    lesson = Lesson(
        curriculum_subject_id=curriculum_subject.id,
        lesson_number=number,
        date=lesson_date,
        topic=clean_topic,
        hours=lesson_hours,
        lesson_type=lesson_type,
        notes=_normalize_notes(notes),
    )
    session.add(lesson)
    _commit(session)
    return lesson


def update_lesson(
    session: Session,
    lesson: Lesson,
    lesson_number: int | str,
    lesson_date: date | None,
    topic: str,
    hours: int | str,
    lesson_type: str | None,
    notes: str | None = None,
) -> Lesson:
    curriculum_subject = session.get(CurriculumSubject, lesson.curriculum_subject_id)
    if curriculum_subject is None:
        raise LessonError(
            "Предмет учебного плана для занятия больше недоступен."
        )

    number = _validate_positive_int(lesson_number, "Номер занятия")
    lesson_hours = _validate_positive_int(hours, "Часы")
    _validate_date(lesson_date)
    clean_topic = _validate_topic(topic)
    _validate_lesson_type(lesson_type)
    _validate_allocated_hours(
        session, curriculum_subject, lesson_hours, exclude_lesson_id=lesson.id
    )

    lesson.lesson_number = number
    lesson.date = lesson_date
    lesson.topic = clean_topic
    lesson.hours = lesson_hours
    lesson.lesson_type = lesson_type
    lesson.notes = _normalize_notes(notes)
    _commit(session)
    return lesson


def delete_lesson(session: Session, lesson: Lesson) -> None:
    session.delete(lesson)
    _commit(session)


def _validate_positive_int(value: int | str, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise LessonError(f"{label}: укажите целое положительное число.")

    try:
        result = int(str(value).strip())
    except (TypeError, ValueError) as error:
        raise LessonError(
            f"{label}: укажите целое положительное число."
        ) from error

    if result <= 0:
        raise LessonError(f"{label}: укажите целое положительное число.")
    return result


def _validate_date(value: date | None) -> None:
    if not isinstance(value, date):
        raise LessonError("Укажите дату.")


def _validate_topic(topic: str) -> str:
    if not isinstance(topic, str) or not topic.strip():
        raise LessonError("Укажите тему.")
    return topic.strip()


def _validate_lesson_type(lesson_type: str | None) -> None:
    if lesson_type not in LESSON_TYPES:
        raise LessonError("Выберите тип занятия.")


def _validate_allocated_hours(
    session: Session,
    curriculum_subject: CurriculumSubject,
    lesson_hours: int,
    exclude_lesson_id: int | None = None,
) -> None:
    allocated = allocated_lesson_hours(
        session, curriculum_subject.id, exclude_lesson_id=exclude_lesson_id
    )
    if allocated + lesson_hours > curriculum_subject.hours:
        remaining = curriculum_subject.hours - allocated
        raise LessonError(
            f"Добавление {lesson_hours} ч. превысит плановые "
            f"{curriculum_subject.hours} ч. "
            f"Доступно ещё {remaining} ч."
        )


def _normalize_notes(notes: str | None) -> str | None:
    if notes is None:
        return None
    clean_notes = notes.strip()
    return clean_notes or None


def _commit(session: Session) -> None:
    try:
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        raise LessonError(
            "Не удалось сохранить занятие из-за ошибки базы данных. "
            "Попробуйте ещё раз."
        ) from error
