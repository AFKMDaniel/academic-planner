import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Curriculum, CurriculumSubject, Subject
from app.services.subject_service import (
    SubjectError,
    create_subject,
    delete_subject,
    list_subjects,
    update_subject,
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


def test_create_subject(session: Session):
    subject = create_subject(session, "Programming", "PRG")

    assert subject.id is not None
    assert subject.name == "Programming"
    assert subject.code == "PRG"
    assert list_subjects(session) == [subject]


def test_create_subject_trims_input(session: Session):
    subject = create_subject(session, "  Math  ", "  MTH  ")

    assert subject.name == "Math"
    assert subject.code == "MTH"


@pytest.mark.parametrize(
    "name, code",
    [
        ("", "PRG"),
        ("   ", "PRG"),
        ("Programming", ""),
        ("Programming", "   "),
    ],
)
def test_create_subject_validation(session: Session, name, code):
    with pytest.raises(SubjectError):
        create_subject(session, name, code)
    assert list_subjects(session) == []


def test_create_subject_rejects_duplicate_code(session: Session):
    create_subject(session, "Programming", "PRG")

    with pytest.raises(SubjectError):
        create_subject(session, "Other", "prg")


def test_update_subject(session: Session):
    subject = create_subject(session, "Programming", "PRG")

    update_subject(session, subject, "Algorithms", "ALG")

    assert subject.name == "Algorithms"
    assert subject.code == "ALG"


def test_update_subject_keeps_own_code(session: Session):
    subject = create_subject(session, "Programming", "PRG")

    update_subject(session, subject, "Programming Basics", "PRG")

    assert subject.code == "PRG"


def test_update_subject_rejects_duplicate_code(session: Session):
    create_subject(session, "Programming", "PRG")
    subject = create_subject(session, "Algorithms", "ALG")

    with pytest.raises(SubjectError):
        update_subject(session, subject, "Algorithms", "PRG")


def test_delete_subject(session: Session):
    subject = create_subject(session, "Programming", "PRG")

    delete_subject(session, subject)

    assert list_subjects(session) == []


def test_delete_subject_in_use_is_blocked(session: Session):
    curriculum = Curriculum(academic_year="2026/2027", group_name="IS-21")
    subject = create_subject(session, "Programming", "PRG")
    session.add(CurriculumSubject(curriculum=curriculum, subject=subject, hours=72))
    session.commit()

    with pytest.raises(SubjectError):
        delete_subject(session, subject)

    assert list_subjects(session) == [subject]
