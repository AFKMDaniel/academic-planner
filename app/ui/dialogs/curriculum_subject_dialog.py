from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from app.models import Curriculum
from app.services.curriculum_subject_service import (
    CurriculumSubjectError,
    add_curriculum_subject,
    list_available_subjects,
)


class CurriculumSubjectDialog(QDialog):
    """Form used to add a subject to a curriculum."""

    def __init__(
        self,
        session: Session,
        curriculum: Curriculum,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._session = session
        self._curriculum = curriculum

        self.setWindowTitle("Добавление предмета в учебный план")
        self.setModal(True)
        self.setMinimumWidth(360)

        self._build_ui()
        self._load_subjects()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        self.subject_combo = QComboBox()

        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(1, 9999)
        self.hours_spin.setValue(1)

        form.addRow("Предмет", self.subject_combo)
        form.addRow("Плановые часы", self.hours_spin)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_subjects(self) -> None:
        for subject in list_available_subjects(self._session, self._curriculum.id):
            self.subject_combo.addItem(f"{subject.name} ({subject.code})", subject.id)

    def _on_save(self) -> None:
        try:
            add_curriculum_subject(
                self._session,
                self._curriculum,
                self.subject_combo.currentData(),
                self.hours_spin.value(),
            )
        except CurriculumSubjectError as error:
            QMessageBox.warning(self, "Некорректные данные", str(error))
            return

        self.accept()
