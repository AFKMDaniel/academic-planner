from sqlalchemy import func, inspect, select
from sqlalchemy.orm import Session

from app.database.connection import engine
from app.models import Base, Curriculum, CurriculumSubject, Lesson, Subject


def init_database() -> None:
    _drop_subject_total_hours_column()
    Base.metadata.create_all(engine)


def _drop_subject_total_hours_column() -> None:
    inspector = inspect(engine)
    if "subjects" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("subjects")}
    if "total_hours" not in columns:
        return

    connection = engine.connect().execution_options(isolation_level="AUTOCOMMIT")
    with connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        connection.exec_driver_sql("DROP TABLE IF EXISTS subjects_new")
        connection.exec_driver_sql(
            """
            CREATE TABLE subjects_new (
                id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                code VARCHAR(50) NOT NULL,
                PRIMARY KEY (id),
                UNIQUE (code)
            )
            """
        )
        connection.exec_driver_sql(
            "INSERT INTO subjects_new (id, name, code) "
            "SELECT id, name, code FROM subjects"
        )
        connection.exec_driver_sql("DROP TABLE subjects")
        connection.exec_driver_sql("ALTER TABLE subjects_new RENAME TO subjects")
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


def is_database_empty(session: Session) -> bool:
    models = (Curriculum, Subject, CurriculumSubject, Lesson)
    return all(
        session.scalar(select(func.count()).select_from(model)) == 0
        for model in models
    )
