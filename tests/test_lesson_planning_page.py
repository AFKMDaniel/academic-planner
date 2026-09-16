import os
from datetime import date

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.services.curriculum_service import create_curriculum
from app.services.curriculum_subject_service import add_curriculum_subject
from app.services.lesson_service import add_lesson, delete_lesson, update_lesson
from app.services.subject_service import create_subject
from app.ui.pages.lesson_planning_page import LessonPlanningPage


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


@pytest.fixture(scope="module")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def page(qt_app, session: Session) -> LessonPlanningPage:
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    add_curriculum_subject(session, curriculum, subject.id, 10)

    lesson_page = LessonPlanningPage(session=session)
    lesson_page.refresh()
    lesson_page.curriculum_combo.setCurrentIndex(0)
    lesson_page.subject_combo.setCurrentIndex(0)
    return lesson_page


def test_summary_without_lessons(page: LessonPlanningPage):
    assert page.planned_hours_value.text() == "10"
    assert page.allocated_hours_value.text() == "0"
    assert page.remaining_hours_value.text() == "10"


def test_summary_updates_after_create_edit_and_delete(
    page: LessonPlanningPage, session: Session
):
    curriculum_subject_id = page.subject_combo.currentData()

    lesson = add_lesson(
        session, curriculum_subject_id, 1, date(2026, 9, 1), "Intro", 4, "Lecture"
    )
    page._load_lessons()
    assert page.allocated_hours_value.text() == "4"
    assert page.remaining_hours_value.text() == "6"

    update_lesson(session, lesson, 1, date(2026, 9, 1), "Intro", 2, "Lecture")
    page._load_lessons()
    assert page.allocated_hours_value.text() == "2"
    assert page.remaining_hours_value.text() == "8"

    delete_lesson(session, lesson)
    page._load_lessons()
    assert page.allocated_hours_value.text() == "0"
    assert page.remaining_hours_value.text() == "10"


def test_summary_resets_when_subject_is_cleared(page: LessonPlanningPage):
    page.subject_combo.setCurrentIndex(-1)
    assert page.planned_hours_value.text() == "—"
    assert page.allocated_hours_value.text() == "—"
    assert page.remaining_hours_value.text() == "—"
