from datetime import date

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Curriculum, CurriculumSubject, Lesson, Subject
from app.services.curriculum_service import (
    CurriculumError,
    count_curriculum_subjects,
    create_curriculum,
    delete_curriculum,
    list_curricula,
    update_curriculum,
)


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


def test_create_curriculum(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")

    assert curriculum.id is not None
    assert curriculum.academic_year == "2026/2027"
    assert curriculum.group_name == "IS-21"
    assert list_curricula(session) == [curriculum]


def test_create_curriculum_trims_input(session: Session):
    curriculum = create_curriculum(session, "  2026/2027  ", "  IS-21  ")

    assert curriculum.academic_year == "2026/2027"
    assert curriculum.group_name == "IS-21"


@pytest.mark.parametrize(
    "academic_year, group_name",
    [
        ("", "IS-21"),
        ("   ", "IS-21"),
        ("2026/2027", ""),
        ("2026/2027", "   "),
    ],
)
def test_create_curriculum_validation(session: Session, academic_year, group_name):
    with pytest.raises(CurriculumError):
        create_curriculum(session, academic_year, group_name)
    assert list_curricula(session) == []


def test_create_curriculum_rejects_duplicate(session: Session):
    create_curriculum(session, "2026/2027", "IS-21")

    with pytest.raises(CurriculumError):
        create_curriculum(session, "2026/2027", "is-21")


def test_update_curriculum(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")

    update_curriculum(session, curriculum, "2027/2028", "IS-22")

    assert curriculum.academic_year == "2027/2028"
    assert curriculum.group_name == "IS-22"


def test_update_curriculum_keeps_own_values(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")

    update_curriculum(session, curriculum, "2026/2027", "IS-21")

    assert curriculum.academic_year == "2026/2027"
    assert curriculum.group_name == "IS-21"


def test_update_curriculum_rejects_duplicate(session: Session):
    create_curriculum(session, "2026/2027", "IS-21")
    curriculum = create_curriculum(session, "2027/2028", "IS-22")

    with pytest.raises(CurriculumError):
        update_curriculum(session, curriculum, "2026/2027", "IS-21")


def test_delete_curriculum(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")

    delete_curriculum(session, curriculum)

    assert list_curricula(session) == []


def test_delete_curriculum_removes_related_subjects_and_lessons(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = Subject(name="Programming", code="PRG")
    curriculum_subject = CurriculumSubject(
        curriculum=curriculum, subject=subject, hours=72
    )
    lesson = Lesson(
        curriculum_subject=curriculum_subject,
        lesson_number=1,
        date=date(2026, 9, 1),
        topic="Introduction to Programming",
        hours=2,
        lesson_type="Lecture",
    )
    session.add_all([subject, curriculum_subject, lesson])
    session.commit()

    assert count_curriculum_subjects(session, curriculum.id) == 1

    delete_curriculum(session, curriculum)

    assert list_curricula(session) == []
    assert session.scalar(select(func.count()).select_from(CurriculumSubject)) == 0
    assert session.scalar(select(func.count()).select_from(Lesson)) == 0
    assert session.scalar(select(func.count()).select_from(Subject)) == 1
