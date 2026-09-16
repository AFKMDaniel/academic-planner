from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Curriculum, CurriculumSubject, Lesson, Subject
from app.services.demo_data import seed_demo_data


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)()


def count(session: Session, model) -> int:
    return session.scalar(select(func.count()).select_from(model))


def test_seed_demo_data_populates_empty_database():
    session = make_session()
    try:
        assert seed_demo_data(session) is True
        assert count(session, Curriculum) == 1
        assert count(session, Subject) == 1
        assert count(session, CurriculumSubject) == 1
        assert count(session, Lesson) == 4
    finally:
        session.close()


def test_seed_demo_data_does_not_duplicate():
    session = make_session()
    try:
        assert seed_demo_data(session) is True
        assert seed_demo_data(session) is False
        assert count(session, Curriculum) == 1
        assert count(session, Subject) == 1
        assert count(session, CurriculumSubject) == 1
        assert count(session, Lesson) == 4
    finally:
        session.close()
