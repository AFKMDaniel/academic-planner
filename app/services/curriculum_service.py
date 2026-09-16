from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Curriculum, CurriculumSubject


class CurriculumError(Exception):
    """Raised when a curriculum operation violates a validation or usage rule."""


def list_curricula(session: Session) -> list[Curriculum]:
    return list(
        session.scalars(
            select(Curriculum).order_by(
                Curriculum.academic_year, Curriculum.group_name, Curriculum.id
            )
        )
    )


def get_curriculum(session: Session, curriculum_id: int) -> Curriculum | None:
    return session.get(Curriculum, curriculum_id)


def create_curriculum(
    session: Session, academic_year: str, group_name: str
) -> Curriculum:
    academic_year, group_name = _normalize(academic_year, group_name)
    _validate(academic_year, group_name)
    _ensure_unique(session, academic_year, group_name)

    curriculum = Curriculum(academic_year=academic_year, group_name=group_name)
    session.add(curriculum)
    _commit(session)
    return curriculum


def update_curriculum(
    session: Session,
    curriculum: Curriculum,
    academic_year: str,
    group_name: str,
) -> Curriculum:
    academic_year, group_name = _normalize(academic_year, group_name)
    _validate(academic_year, group_name)
    _ensure_unique(session, academic_year, group_name, exclude_id=curriculum.id)

    curriculum.academic_year = academic_year
    curriculum.group_name = group_name
    _commit(session)
    return curriculum


def delete_curriculum(session: Session, curriculum: Curriculum) -> None:
    session.delete(curriculum)
    _commit(session)


def count_curriculum_subjects(session: Session, curriculum_id: int) -> int:
    return session.scalar(
        select(func.count())
        .select_from(CurriculumSubject)
        .where(CurriculumSubject.curriculum_id == curriculum_id)
    )


def _normalize(academic_year: str, group_name: str) -> tuple[str, str]:
    return academic_year.strip(), group_name.strip()


def _validate(academic_year: str, group_name: str) -> None:
    if not academic_year:
        raise CurriculumError("Укажите учебный год.")
    if not group_name:
        raise CurriculumError("Укажите группу.")


def _ensure_unique(
    session: Session,
    academic_year: str,
    group_name: str,
    exclude_id: int | None = None,
) -> None:
    query = select(Curriculum.id).where(
        func.lower(Curriculum.academic_year) == academic_year.lower(),
        func.lower(Curriculum.group_name) == group_name.lower(),
    )
    if exclude_id is not None:
        query = query.where(Curriculum.id != exclude_id)
    if session.scalar(query) is not None:
        raise CurriculumError(
            f"Учебный план для группы «{group_name}» на {academic_year} "
            "учебный год уже существует."
        )


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise CurriculumError(
            "Не удалось сохранить учебный план. Возможно, он уже существует."
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise CurriculumError(
            "Не удалось сохранить учебный план из-за ошибки базы данных. "
            "Попробуйте ещё раз."
        ) from error
