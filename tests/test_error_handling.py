import os
import sys
from datetime import date

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import main as app_main
from app.models import Base
from app.services.curriculum_service import CurriculumError, create_curriculum
from app.services.curriculum_subject_service import (
    CurriculumSubjectError,
    add_curriculum_subject,
)
from app.services.lesson_service import LessonError, add_lesson
from app.services.subject_service import SubjectError, create_subject
from app.ui.error_handling import _handle_exception, install_exception_hook


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


def fail_commit(*args, **kwargs):
    raise SQLAlchemyError("database is unavailable")


def test_subject_commit_error_becomes_domain_error(session: Session, monkeypatch):
    monkeypatch.setattr(session, "commit", fail_commit)

    with pytest.raises(SubjectError, match="базы данных"):
        create_subject(session, "Programming", "PRG")


def test_curriculum_commit_error_becomes_domain_error(session: Session, monkeypatch):
    monkeypatch.setattr(session, "commit", fail_commit)

    with pytest.raises(CurriculumError, match="базы данных"):
        create_curriculum(session, "2026/2027", "IS-21")


def test_curriculum_subject_commit_error_becomes_domain_error(
    session: Session, monkeypatch
):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    monkeypatch.setattr(session, "commit", fail_commit)

    with pytest.raises(CurriculumSubjectError, match="базы данных"):
        add_curriculum_subject(session, curriculum, subject.id, 72)


def test_lesson_commit_error_becomes_domain_error(session: Session, monkeypatch):
    curriculum = create_curriculum(session, "2026/2027", "IS-21")
    subject = create_subject(session, "Programming", "PRG")
    curriculum_subject = add_curriculum_subject(session, curriculum, subject.id, 72)
    monkeypatch.setattr(session, "commit", fail_commit)

    with pytest.raises(LessonError, match="базы данных"):
        add_lesson(
            session,
            curriculum_subject.id,
            1,
            date(2026, 9, 1),
            "Topic",
            2,
            "Lecture",
        )


def test_exception_hook_shows_friendly_dialog(qt_app, monkeypatch):
    calls = []
    monkeypatch.setattr(
        QMessageBox, "critical", lambda *args: calls.append(args)
    )

    try:
        raise RuntimeError("boom")
    except RuntimeError as error:
        _handle_exception(type(error), error, error.__traceback__)

    assert calls
    _parent, title, message = calls[0]
    assert title == "Непредвиденная ошибка"
    assert "Traceback" not in message
    assert "RuntimeError" not in message


def test_exception_hook_delegates_keyboard_interrupt(qt_app, monkeypatch):
    delegated = []
    monkeypatch.setattr(sys, "__excepthook__", lambda *args: delegated.append(args))

    try:
        raise KeyboardInterrupt
    except KeyboardInterrupt as error:
        _handle_exception(type(error), error, error.__traceback__)

    assert delegated


def test_install_exception_hook_registers_handler(monkeypatch):
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    install_exception_hook()
    assert sys.excepthook is _handle_exception


def test_prepare_database_reports_startup_failure(qt_app, monkeypatch):
    calls = []
    monkeypatch.setattr(
        app_main,
        "init_database",
        lambda: (_ for _ in ()).throw(SQLAlchemyError("nope")),
    )
    monkeypatch.setattr(QMessageBox, "critical", lambda *args: calls.append(args))

    assert app_main._prepare_database() is False
    assert calls
