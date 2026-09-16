from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.curriculum_subject import CurriculumSubject


LESSON_TYPES = ("Lecture", "Practical", "Laboratory", "Test")


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (
        CheckConstraint(
            "lesson_type IN ('Lecture', 'Practical', 'Laboratory', 'Test')",
            name="ck_lessons_type",
        ),
        CheckConstraint("lesson_number > 0", name="ck_lessons_number_positive"),
        CheckConstraint("hours > 0", name="ck_lessons_hours_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    curriculum_subject_id: Mapped[int] = mapped_column(
        ForeignKey("curriculum_subjects.id", ondelete="CASCADE"), nullable=False
    )
    lesson_number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    topic: Mapped[str] = mapped_column(String(255), nullable=False)
    hours: Mapped[int] = mapped_column(Integer, nullable=False)
    lesson_type: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    curriculum_subject: Mapped["CurriculumSubject"] = relationship(
        back_populates="lessons"
    )

    def __repr__(self) -> str:
        return (
            f"Lesson(id={self.id!r}, lesson_number={self.lesson_number!r}, "
            f"topic={self.topic!r})"
        )
