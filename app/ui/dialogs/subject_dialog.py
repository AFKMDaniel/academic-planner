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

from app.models import Subject
from app.services.subject_service import (
    SubjectError,
    create_subject,
    update_subject,
)


class SubjectDialog(QDialog):
    """Form used to create a new subject or edit an existing one."""

    def __init__(
        self,
        session: Session,
        subject: Subject | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._session = session
        self._subject = subject

        self.setWindowTitle("Изменение предмета" if subject else "Создание предмета")
        self.setModal(True)
        self.setMinimumWidth(360)

        self._build_ui()

        if subject is not None:
            self._load(subject)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("например, Программирование")

        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("например, PRG")

        form.addRow("Название", self.name_edit)
        form.addRow("Код", self.code_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, subject: Subject) -> None:
        self.name_edit.setText(subject.name)
        self.code_edit.setText(subject.code)

    def _on_save(self) -> None:
        try:
            if self._subject is None:
                create_subject(
                    self._session,
                    self.name_edit.text(),
                    self.code_edit.text(),
                )
            else:
                update_subject(
                    self._session,
                    self._subject,
                    self.name_edit.text(),
                    self.code_edit.text(),
                )
        except SubjectError as error:
            QMessageBox.warning(self, "Некорректные данные", str(error))
            return

        self.accept()
