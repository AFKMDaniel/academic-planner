from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import CurriculumSubject, Subject


class SubjectError(Exception):
    """Raised when a subject operation violates a validation or usage rule."""


def list_subjects(session: Session) -> list[Subject]:
    return list(session.scalars(select(Subject).order_by(Subject.name, Subject.id)))


def get_subject(session: Session, subject_id: int) -> Subject | None:
    return session.get(Subject, subject_id)


def create_subject(session: Session, name: str, code: str) -> Subject:
    name, code = _normalize(name, code)
    _validate(name, code)
    _ensure_code_available(session, code)

    subject = Subject(name=name, code=code)
    session.add(subject)
    _commit(session)
    return subject


def update_subject(
    session: Session, subject: Subject, name: str, code: str
) -> Subject:
    name, code = _normalize(name, code)
    _validate(name, code)
    _ensure_code_available(session, code, exclude_id=subject.id)

    subject.name = name
    subject.code = code
    _commit(session)
    return subject


def delete_subject(session: Session, subject: Subject) -> None:
    if _count_curriculum_references(session, subject.id):
        raise SubjectError(
            "Этот предмет используется в одном или нескольких учебных планах, "
            "поэтому его нельзя удалить. Сначала уберите его из этих "
            "учебных планов."
        )

    session.delete(subject)
    _commit(session)


def _normalize(name: str, code: str) -> tuple[str, str]:
    return name.strip(), code.strip()


def _validate(name: str, code: str) -> None:
    if not name:
        raise SubjectError("Укажите название.")
    if not code:
        raise SubjectError("Укажите код.")


def _ensure_code_available(
    session: Session, code: str, exclude_id: int | None = None
) -> None:
    query = select(Subject.id).where(func.lower(Subject.code) == code.lower())
    if exclude_id is not None:
        query = query.where(Subject.id != exclude_id)
    if session.scalar(query) is not None:
        raise SubjectError(f"Предмет с кодом «{code}» уже существует.")


def _count_curriculum_references(session: Session, subject_id: int) -> int:
    return session.scalar(
        select(func.count())
        .select_from(CurriculumSubject)
        .where(CurriculumSubject.subject_id == subject_id)
    )


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise SubjectError(
            "Не удалось сохранить предмет. Возможно, код уже используется."
        ) from error
    except SQLAlchemyError as error:
        session.rollback()
        raise SubjectError(
            "Не удалось сохранить предмет из-за ошибки базы данных. "
            "Попробуйте ещё раз."
        ) from error
