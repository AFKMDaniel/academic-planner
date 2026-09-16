from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.curriculum import Curriculum
    from app.models.lesson import Lesson
    from app.models.subject import Subject


class CurriculumSubject(Base):
    __tablename__ = "curriculum_subjects"
    __table_args__ = (
        UniqueConstraint(
            "curriculum_id", "subject_id", name="uq_curriculum_subjects_pair"
        ),
        CheckConstraint("hours > 0", name="ck_curriculum_subjects_hours_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    curriculum_id: Mapped[int] = mapped_column(
        ForeignKey("curricula.id", ondelete="CASCADE"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(
        ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False
    )
    hours: Mapped[int] = mapped_column(Integer, nullable=False)

    curriculum: Mapped["Curriculum"] = relationship(
        back_populates="curriculum_subjects"
    )
    subject: Mapped["Subject"] = relationship(back_populates="curriculum_subjects")
    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="curriculum_subject",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"CurriculumSubject(id={self.id!r}, curriculum_id={self.curriculum_id!r}, "
            f"subject_id={self.subject_id!r}, hours={self.hours!r})"
        )
