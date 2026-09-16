from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Curriculum, CurriculumSubject, Subject
from app.services.curriculum_service import create_curriculum
from app.services.curriculum_subject_service import add_curriculum_subject
from app.services.lesson_service import (
    LessonError,
    add_lesson,
    delete_lesson,
    list_lessons,
    update_lesson,
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


@pytest.fixture
def curriculum_subject(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    return add_curriculum_subject(session, curriculum, subject.id, 10)


def test_add_lesson(session: Session, curriculum_subject):
    lesson = add_lesson(
        session,
        curriculum_subject.id,
        1,
        date(2026, 9, 1),
        "Introduction to Programming",
        2,
        "Lecture",
        "Bring the syllabus",
    )

    assert lesson.id is not None
    assert lesson.curriculum_subject_id == curriculum_subject.id
    assert lesson.lesson_number == 1
    assert lesson.date == date(2026, 9, 1)
    assert lesson.topic == "Introduction to Programming"
    assert lesson.hours == 2
    assert lesson.lesson_type == "Lecture"
    assert lesson.notes == "Bring the syllabus"
    assert list_lessons(session, curriculum_subject.id) == [lesson]


def test_add_lesson_trims_topic_and_treats_blank_notes_as_none(
    session: Session, curriculum_subject
):
    lesson = add_lesson(
        session,
        curriculum_subject.id,
        1,
        date(2026, 9, 1),
        "  Control Flow  ",
        2,
        "Practical",
        "   ",
    )

    assert lesson.topic == "Control Flow"
    assert lesson.notes is None


@pytest.mark.parametrize("lesson_number", [0, -1, "abc", "1.5", None])
def test_add_lesson_rejects_invalid_number(
    session: Session, curriculum_subject, lesson_number
):
    with pytest.raises(LessonError):
        add_lesson(
            session,
            curriculum_subject.id,
            lesson_number,
            date(2026, 9, 1),
            "Topic",
            2,
            "Lecture",
        )

    assert list_lessons(session, curriculum_subject.id) == []


@pytest.mark.parametrize("hours", [0, -1, "abc", "1.5", None])
def test_add_lesson_rejects_invalid_hours(
    session: Session, curriculum_subject, hours
):
    with pytest.raises(LessonError):
        add_lesson(
            session,
            curriculum_subject.id,
            1,
            date(2026, 9, 1),
            "Topic",
            hours,
            "Lecture",
        )

    assert list_lessons(session, curriculum_subject.id) == []


def test_add_lesson_requires_date(session: Session, curriculum_subject):
    with pytest.raises(LessonError):
        add_lesson(
            session,
            curriculum_subject.id,
            1,
            None,
            "Topic",
            2,
            "Lecture",
        )

    assert list_lessons(session, curriculum_subject.id) == []


@pytest.mark.parametrize("topic", ["", "   ", None])
def test_add_lesson_requires_topic(session: Session, curriculum_subject, topic):
    with pytest.raises(LessonError):
        add_lesson(
            session,
            curriculum_subject.id,
            1,
            date(2026, 9, 1),
            topic,
            2,
            "Lecture",
        )

    assert list_lessons(session, curriculum_subject.id) == []


@pytest.mark.parametrize("lesson_type", [None, "", "Seminar"])
def test_add_lesson_requires_known_type(
    session: Session, curriculum_subject, lesson_type
):
    with pytest.raises(LessonError):
        add_lesson(
            session,
            curriculum_subject.id,
            1,
            date(2026, 9, 1),
            "Topic",
            2,
            lesson_type,
        )

    assert list_lessons(session, curriculum_subject.id) == []


def test_add_lesson_requires_existing_curriculum_subject(session: Session):
    with pytest.raises(LessonError):
        add_lesson(
            session,
            999,
            1,
            date(2026, 9, 1),
            "Topic",
            2,
            "Lecture",
        )


def test_add_lesson_requires_curriculum_subject(session: Session):
    with pytest.raises(LessonError):
        add_lesson(
            session,
            None,
            1,
            date(2026, 9, 1),
            "Topic",
            2,
            "Lecture",
        )


def test_add_lesson_blocks_exceeding_planned_hours(
    session: Session, curriculum_subject
):
    add_lesson(
        session,
        curriculum_subject.id,
        1,
        date(2026, 9, 1),
        "First",
        8,
        "Lecture",
    )

    with pytest.raises(LessonError):
        add_lesson(
            session,
            curriculum_subject.id,
            2,
            date(2026, 9, 8),
            "Second",
            4,
            "Practical",
        )

    assert len(list_lessons(session, curriculum_subject.id)) == 1


def test_add_lesson_allows_exactly_remaining_hours(
    session: Session, curriculum_subject
):
    add_lesson(
        session,
        curriculum_subject.id,
        1,
        date(2026, 9, 1),
        "First",
        8,
        "Lecture",
    )

    lesson = add_lesson(
        session,
        curriculum_subject.id,
        2,
        date(2026, 9, 8),
        "Second",
        2,
        "Test",
    )

    assert lesson.hours == 2
    assert len(list_lessons(session, curriculum_subject.id)) == 2


def test_list_lessons_orders_by_number(session: Session, curriculum_subject):
    add_lesson(
        session, curriculum_subject.id, 2, date(2026, 9, 8), "Second", 1, "Lecture"
    )
    add_lesson(
        session, curriculum_subject.id, 1, date(2026, 9, 1), "First", 1, "Lecture"
    )

    lessons = list_lessons(session, curriculum_subject.id)

    assert [lesson.lesson_number for lesson in lessons] == [1, 2]


def test_update_lesson_changes_editable_fields(
    session: Session, curriculum_subject
):
    lesson = add_lesson(
        session,
        curriculum_subject.id,
        1,
        date(2026, 9, 1),
        "Introduction",
        2,
        "Lecture",
        "Original notes",
    )

    updated = update_lesson(
        session,
        lesson,
        3,
        date(2026, 9, 15),
        "  Control Flow  ",
        4,
        "Practical",
        "   ",
    )

    assert updated.id == lesson.id
    assert updated.curriculum_subject_id == curriculum_subject.id
    assert updated.lesson_number == 3
    assert updated.date == date(2026, 9, 15)
    assert updated.topic == "Control Flow"
    assert updated.hours == 4
    assert updated.lesson_type == "Practical"
    assert updated.notes is None


@pytest.mark.parametrize("lesson_number", [0, -1, "abc", "1.5", None])
def test_update_lesson_rejects_invalid_number(
    session: Session, curriculum_subject, lesson_number
):
    lesson = add_lesson(
        session, curriculum_subject.id, 1, date(2026, 9, 1), "Topic", 2, "Lecture"
    )

    with pytest.raises(LessonError):
        update_lesson(
            session,
            lesson,
            lesson_number,
            date(2026, 9, 8),
            "Changed",
            2,
            "Lecture",
        )

    assert lesson.lesson_number == 1
    assert lesson.topic == "Topic"


@pytest.mark.parametrize("hours", [0, -1, "abc", "1.5", None])
def test_update_lesson_rejects_invalid_hours(
    session: Session, curriculum_subject, hours
):
    lesson = add_lesson(
        session, curriculum_subject.id, 1, date(2026, 9, 1), "Topic", 2, "Lecture"
    )

    with pytest.raises(LessonError):
        update_lesson(
            session,
            lesson,
            1,
            date(2026, 9, 1),
            "Topic",
            hours,
            "Lecture",
        )

    assert lesson.hours == 2


def test_update_lesson_requires_date(session: Session, curriculum_subject):
    lesson = add_lesson(
        session, curriculum_subject.id, 1, date(2026, 9, 1), "Topic", 2, "Lecture"
    )

    with pytest.raises(LessonError):
        update_lesson(
            session, lesson, 1, None, "Topic", 2, "Lecture"
        )

    assert lesson.date == date(2026, 9, 1)


@pytest.mark.parametrize("topic", ["", "   ", None])
def test_update_lesson_requires_topic(
    session: Session, curriculum_subject, topic
):
    lesson = add_lesson(
        session, curriculum_subject.id, 1, date(2026, 9, 1), "Topic", 2, "Lecture"
    )

    with pytest.raises(LessonError):
        update_lesson(
            session, lesson, 1, date(2026, 9, 1), topic, 2, "Lecture"
        )

    assert lesson.topic == "Topic"


@pytest.mark.parametrize("lesson_type", [None, "", "Seminar"])
def test_update_lesson_requires_known_type(
    session: Session, curriculum_subject, lesson_type
):
    lesson = add_lesson(
        session, curriculum_subject.id, 1, date(2026, 9, 1), "Topic", 2, "Lecture"
    )

    with pytest.raises(LessonError):
        update_lesson(
            session,
            lesson,
            1,
            date(2026, 9, 1),
            "Topic",
            2,
            lesson_type,
        )

    assert lesson.lesson_type == "Lecture"


def test_update_lesson_excludes_current_lesson_from_allocated_hours(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, 72)

    add_lesson(
        session,
        curriculum_subject.id,
        1,
        date(2026, 9, 1),
        "First",
        60,
        "Lecture",
    )
    current = add_lesson(
        session,
        curriculum_subject.id,
        2,
        date(2026, 9, 8),
        "Second",
        2,
        "Practical",
    )

    updated = update_lesson(
        session,
        current,
        2,
        date(2026, 9, 8),
        "Second",
        10,
        "Practical",
    )

    assert updated.hours == 10
    assert sum(lesson.hours for lesson in list_lessons(
        session, curriculum_subject.id
    )) == 70


def test_update_lesson_blocks_exceeding_planned_hours(session: Session):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, 72)

    add_lesson(
        session,
        curriculum_subject.id,
        1,
        date(2026, 9, 1),
        "First",
        60,
        "Lecture",
    )
    current = add_lesson(
        session,
        curriculum_subject.id,
        2,
        date(2026, 9, 8),
        "Second",
        2,
        "Practical",
    )

    with pytest.raises(LessonError):
        update_lesson(
            session,
            current,
            2,
            date(2026, 9, 8),
            "Second",
            15,
            "Practical",
        )

    assert current.hours == 2
    assert sum(lesson.hours for lesson in list_lessons(
        session, curriculum_subject.id
    )) == 62


def test_delete_lesson_removes_only_the_lesson(
    session: Session, curriculum_subject
):
    first = add_lesson(
        session, curriculum_subject.id, 1, date(2026, 9, 1), "First", 2, "Lecture"
    )
    second = add_lesson(
        session, curriculum_subject.id, 2, date(2026, 9, 8), "Second", 3, "Practical"
    )

    delete_lesson(session, first)

    assert list_lessons(session, curriculum_subject.id) == [second]
    assert session.get(CurriculumSubject, curriculum_subject.id) is not None
    assert session.get(Subject, curriculum_subject.subject_id) is not None
    assert session.get(Curriculum, curriculum_subject.curriculum_id) is not None


def test_delete_lesson_recalculates_allocated_hours(
    session: Session, curriculum_subject
):
    first = add_lesson(
        session, curriculum_subject.id, 1, date(2026, 9, 1), "First", 4, "Lecture"
    )
    add_lesson(
        session, curriculum_subject.id, 2, date(2026, 9, 8), "Second", 2, "Practical"
    )

    delete_lesson(session, first)

    remaining = list_lessons(session, curriculum_subject.id)
    assert sum(lesson.hours for lesson in remaining) == 2
