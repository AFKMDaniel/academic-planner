from datetime import date

from sqlalchemy.orm import Session

from app.database.init import is_database_empty
from app.models import Curriculum, CurriculumSubject, Lesson, Subject


def seed_demo_data(session: Session) -> bool:
    if not is_database_empty(session):
        return False

    curriculum = Curriculum(academic_year="2026/2027", group_name="IS-21")
    subject = Subject(name="Программирование", code="PRG")
    curriculum_subject = CurriculumSubject(
        curriculum=curriculum,
        subject=subject,
        hours=72,
    )

    lessons = [
        Lesson(
            curriculum_subject=curriculum_subject,
            lesson_number=1,
            date=date(2026, 9, 1),
            topic="Введение в программирование",
            hours=2,
            lesson_type="Lecture",
        ),
        Lesson(
            curriculum_subject=curriculum_subject,
            lesson_number=2,
            date=date(2026, 9, 8),
            topic="Переменные и типы данных",
            hours=2,
            lesson_type="Practical",
        ),
        Lesson(
            curriculum_subject=curriculum_subject,
            lesson_number=3,
            date=date(2026, 9, 15),
            topic="Управляющие конструкции",
            hours=2,
            lesson_type="Lecture",
        ),
        Lesson(
            curriculum_subject=curriculum_subject,
            lesson_number=4,
            date=date(2026, 9, 22),
            topic="Циклы и итерации",
            hours=2,
            lesson_type="Laboratory",
        ),
    ]

    session.add_all([curriculum, subject, curriculum_subject, *lessons])
    session.commit()
    return True
