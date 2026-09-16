from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from app.models import Curriculum
from app.services.curriculum_service import (
    CurriculumError,
    create_curriculum,
    update_curriculum,
)


class CurriculumDialog(QDialog):
    """Form used to create a new curriculum or edit an existing one."""

    def __init__(
        self,
        session: Session,
        curriculum: Curriculum | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._session = session
        self._curriculum = curriculum

        self.setWindowTitle(
            "Изменение учебного плана" if curriculum else "Создание учебного плана"
        )
        self.setModal(True)
        self.setMinimumWidth(360)

        self._build_ui()

        if curriculum is not None:
            self._load(curriculum)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        self.academic_year_edit = QLineEdit()
        self.academic_year_edit.setPlaceholderText("например, 2026/2027")

        self.group_name_edit = QLineEdit()
        self.group_name_edit.setPlaceholderText("например, ИС-21")

        form.addRow("Учебный год", self.academic_year_edit)
        form.addRow("Группа", self.group_name_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, curriculum: Curriculum) -> None:
        self.academic_year_edit.setText(curriculum.academic_year)
        self.group_name_edit.setText(curriculum.group_name)

    def _on_save(self) -> None:
        try:
            if self._curriculum is None:
                create_curriculum(
                    self._session,
                    self.academic_year_edit.text(),
                    self.group_name_edit.text(),
                )
            else:
                update_curriculum(
                    self._session,
                    self._curriculum,
                    self.academic_year_edit.text(),
                    self.group_name_edit.text(),
                )
        except CurriculumError as error:
            QMessageBox.warning(self, "Некорректные данные", str(error))
            return

        self.accept()
