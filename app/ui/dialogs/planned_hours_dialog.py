from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from app.models import CurriculumSubject
from app.services.curriculum_subject_service import (
    CurriculumSubjectError,
    allocated_lesson_hours,
    update_curriculum_subject_hours,
)


class PlannedHoursDialog(QDialog):
    """Form used to change the planned hours of a curriculum subject."""

    def __init__(
        self,
        session: Session,
        curriculum_subject: CurriculumSubject,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._session = session
        self._curriculum_subject = curriculum_subject

        self.setWindowTitle("Изменение плановых часов")
        self.setModal(True)
        self.setMinimumWidth(360)

        self._allocated_hours = allocated_lesson_hours(session, curriculum_subject.id)

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        subject = self._curriculum_subject.subject
        form.addRow("Предмет", QLabel(f"{subject.name} ({subject.code})"))

        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(max(1, self._allocated_hours), 9999)
        self.hours_spin.setValue(self._curriculum_subject.hours)
        form.addRow("Плановые часы", self.hours_spin)
        layout.addLayout(form)

        if self._allocated_hours:
            hint = QLabel(
                f"Уже распределено на занятия: {self._allocated_hours} ч."
            )
            hint.setObjectName("pageSubtitle")
            hint.setWordWrap(True)
            layout.addWidget(hint)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_save(self) -> None:
        try:
            update_curriculum_subject_hours(
                self._session,
                self._curriculum_subject,
                self.hours_spin.value(),
            )
        except CurriculumSubjectError as error:
            QMessageBox.warning(self, "Некорректные данные", str(error))
            return

        self.accept()
