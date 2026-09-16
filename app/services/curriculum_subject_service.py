from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Curriculum, CurriculumSubject, Lesson, Subject


class CurriculumSubjectError(Exception):
    """Raised when a curriculum subject operation violates a validation rule."""


def list_curriculum_subjects(
    session: Session, curriculum_id: int
) -> list[CurriculumSubject]:
    return list(
        session.scalars(
            select(CurriculumSubject)
            .where(CurriculumSubject.curriculum_id == curriculum_id)
            .order_by(CurriculumSubject.id)
        )
    )


def get_curriculum_subject(
    session: Session, curriculum_subject_id: int
) -> CurriculumSubject | None:
    return session.get(CurriculumSubject, curriculum_subject_id)


def list_available_subjects(session: Session, curriculum_id: int) -> list[Subject]:
    """Subjects that are not yet part of the given curriculum."""
    used_subject_ids = select(CurriculumSubject.subject_id).where(
        CurriculumSubject.curriculum_id == curriculum_id
    )
    return list(
        session.scalars(
            select(Subject)
            .where(Subject.id.not_in(used_subject_ids))
            .order_by(Subject.name, Subject.id)
        )
    )


def add_curriculum_subject(
    session: Session,
    curriculum: Curriculum,
    subject_id: int | None,
    hours: int | str,
) -> CurriculumSubject:
    if subject_id is None:
        raise CurriculumSubjectError("Выберите предмет.")

    subject = session.get(Subject, subject_id)
    if subject is None:
        raise CurriculumSubjectError("Выберите корректный предмет.")

    planned_hours = _validate_hours(hours)
    _ensure_not_duplicate(session, curriculum.id, subject_id)

    curriculum_subject = CurriculumSubject(
        curriculum_id=curriculum.id,
        subject_id=subject_id,
        hours=planned_hours,
    )
    session.add(curriculum_subject)
    _commit(session)
    return curriculum_subject


def update_curriculum_subject_hours(
    session: Session,
    curriculum_subject: CurriculumSubject,
    hours: int | str,
) -> CurriculumSubject:
    planned_hours = _validate_hours(hours)
    allocated = allocated_lesson_hours(session, curriculum_subject.id)
    if planned_hours < allocated:
        raise CurriculumSubjectError(
            f"Плановые часы не могут быть меньше {allocated} ч. — "
            "столько уже распределено на занятия."
        )

    curriculum_subject.hours = planned_hours
    _commit(session)
    return curriculum_subject


def remove_curriculum_subject(
    session: Session, curriculum_subject: CurriculumSubject
) -> None:
    """Remove a curriculum subject together with its lessons."""
    session.delete(curriculum_subject)
    _commit(session)


def allocated_lesson_hours(
    session: Session,
    curriculum_subject_id: int,
    exclude_lesson_id: int | None = None,
) -> int:
    query = select(func.coalesce(func.sum(Lesson.hours), 0)).where(
        Lesson.curriculum_subject_id == curriculum_subject_id
    )
    if exclude_lesson_id is not None:
        query = query.where(Lesson.id != exclude_lesson_id)
    return session.scalar(query)


def count_lessons(session: Session, curriculum_subject_id: int) -> int:
    return session.scalar(
        select(func.count())
        .select_from(Lesson)
        .where(Lesson.curriculum_subject_id == curriculum_subject_id)
    )


def _validate_hours(hours: int | str) -> int:
    if isinstance(hours, bool) or not isinstance(hours, (int, str)):
        raise CurriculumSubjectError("Плановые часы должны быть целым положительным числом.")

    try:
        value = int(str(hours).strip())
    except (TypeError, ValueError) as error:
        raise CurriculumSubjectError(
            "Плановые часы должны быть целым положительным числом."
        ) from error

    if value <= 0:
        raise CurriculumSubjectError("Плановые часы должны быть целым положительным числом.")
    return value


def _ensure_not_duplicate(
    session: Session, curriculum_id: int, subject_id: int
) -> None:
    existing = session.scalar(
        select(CurriculumSubject.id).where(
            CurriculumSubject.curriculum_id == curriculum_id,
            CurriculumSubject.subject_id == subject_id,
        )
    )
    if existing is not None:
        raise CurriculumSubjectError("Этот предмет уже включён в учебный план.")


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise CurriculumSubjectError(
            "Не удалось сохранить предмет. Возможно, он уже включён "
            "в учебный план."
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise CurriculumSubjectError(
            "Не удалось сохранить предмет учебного плана из-за ошибки базы "
            "данных. Попробуйте ещё раз."
        ) from error
