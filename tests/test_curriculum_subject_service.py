from datetime import date

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, CurriculumSubject, Lesson, Subject
from app.services.curriculum_service import create_curriculum
from app.services.curriculum_subject_service import (
    CurriculumSubjectError,
    add_curriculum_subject,
    allocated_lesson_hours,
    count_lessons,
    get_curriculum_subject,
    list_available_subjects,
    list_curriculum_subjects,
    remove_curriculum_subject,
    update_curriculum_subject_hours,
)
from app.services.subject_service import create_subject


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    db_session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield db_session
    finally:
        db_session.close()


def add_lessons(session: Session, curriculum_subject, count: int, hours: int) -> None:
    for index in range(count):
        session.add(
            Lesson(
                curriculum_subject=curriculum_subject,
                lesson_number=index + 1,
                date=date(2026, 9, 1),
                topic=f"Lesson {index + 1}",
                hours=hours,
                lesson_type="Lecture",
            )
        )
    session.commit()


def test_add_curriculum_subject(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")

    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, 72)

    assert curriculum_subject.id is not None
    assert curriculum_subject.curriculum_id == curriculum.id
    assert curriculum_subject.subject_id == subject.id
    assert curriculum_subject.hours == 72
    assert list_curriculum_subjects(session, curriculum.id) == [curriculum_subject]


def test_add_curriculum_subject_accepts_numeric_string(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")

    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, "72")

    assert curriculum_subject.hours == 72


@pytest.mark.parametrize("hours", [0, -5, "abc", "3.5", None, 2.5])
def test_add_curriculum_subject_rejects_invalid_hours(session: Session, hours):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")

    with pytest.raises(CurriculumSubjectError):
        add_curriculum_subject(session, curriculum, subject.id, hours)

    assert list_curriculum_subjects(session, curriculum.id) == []


def test_add_curriculum_subject_requires_subject(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")

    with pytest.raises(CurriculumSubjectError):
        add_curriculum_subject(session, curriculum, None, 72)

    assert list_curriculum_subjects(session, curriculum.id) == []


def test_add_curriculum_subject_rejects_unknown_subject(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")

    with pytest.raises(CurriculumSubjectError):
        add_curriculum_subject(session, curriculum, 999, 72)

    assert list_curriculum_subjects(session, curriculum.id) == []


def test_add_curriculum_subject_rejects_duplicate(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    add_curriculum_subject(session, curriculum, subject.id, 72)

    with pytest.raises(CurriculumSubjectError):
        add_curriculum_subject(session, curriculum, subject.id, 36)

    assert len(list_curriculum_subjects(session, curriculum.id)) == 1


def test_list_available_subjects_excludes_used(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    programming = create_subject(session, "Programming", "PRG")
    algorithms = create_subject(session, "Algorithms", "ALG")
    add_curriculum_subject(session, curriculum, programming.id, 72)

    assert list_available_subjects(session, curriculum.id) == [algorithms]


def test_update_curriculum_subject_hours(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, 72)

    update_curriculum_subject_hours(session, curriculum_subject, 90)

    assert curriculum_subject.hours == 90
    assert get_curriculum_subject(session, curriculum_subject.id).hours == 90


def test_update_curriculum_subject_hours_below_allocated_is_blocked(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, 72)
    add_lessons(session, curriculum_subject, count=4, hours=2)

    with pytest.raises(CurriculumSubjectError):
        update_curriculum_subject_hours(session, curriculum_subject, 7)

    assert curriculum_subject.hours == 72


def test_update_curriculum_subject_hours_equal_to_allocated(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, 72)
    add_lessons(session, curriculum_subject, count=4, hours=2)

    update_curriculum_subject_hours(session, curriculum_subject, 8)

    assert curriculum_subject.hours == 8


def test_allocated_lesson_hours_and_count(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, 72)
    add_lessons(session, curriculum_subject, count=4, hours=2)

    assert allocated_lesson_hours(session, curriculum_subject.id) == 8
    assert count_lessons(session, curriculum_subject.id) == 4


def test_remove_curriculum_subject(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, 72)

    remove_curriculum_subject(session, curriculum_subject)

    assert list_curriculum_subjects(session, curriculum.id) == []
    assert session.get(Subject, subject.id) is not None


def test_remove_curriculum_subject_deletes_lessons(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, 72)
    add_lessons(session, curriculum_subject, count=4, hours=2)

    remove_curriculum_subject(session, curriculum_subject)

    assert session.scalar(select(func.count()).select_from(CurriculumSubject)) == 0
    assert session.scalar(select(func.count()).select_from(Lesson)) == 0
