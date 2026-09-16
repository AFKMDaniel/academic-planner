from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.curriculum_subject import CurriculumSubject


class Curriculum(Base):
    __tablename__ = "curricula"
    __table_args__ = (
        UniqueConstraint(
            "academic_year", "group_name", name="uq_curricula_year_group"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    group_name: Mapped[str] = mapped_column(String(100), nullable=False)

    curriculum_subjects: Mapped[list["CurriculumSubject"]] = relationship(
        back_populates="curriculum",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"Curriculum(id={self.id!r}, academic_year={self.academic_year!r}, "
            f"group_name={self.group_name!r})"
        )
