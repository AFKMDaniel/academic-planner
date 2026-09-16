from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from app.models import LESSON_TYPES, CurriculumSubject, Lesson
from app.services.lesson_service import LessonError, add_lesson, update_lesson
from app.ui.lesson_types import lesson_type_label


class LessonDialog(QDialog):
    """Form used to create or edit a lesson of a curriculum subject."""

    def __init__(
        self,
        session: Session,
        curriculum_subject: CurriculumSubject,
        lesson: Lesson | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._session = session
        self._curriculum_subject = curriculum_subject
        self._lesson = lesson

        self.setWindowTitle("Изменение занятия" if lesson else "Создание занятия")
        self.setModal(True)
        self.setMinimumWidth(420)

        self._build_ui()

        if lesson is not None:
            self._load(lesson)

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        form.setSpacing(10)

        self.number_spin = QSpinBox()
        self.number_spin.setRange(1, 9999)
        self.number_spin.setValue(1)

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("dd.MM.yyyy")
        self.date_edit.setDate(QDate.currentDate())

        self.topic_edit = QLineEdit()
        self.topic_edit.setPlaceholderText("например, Введение в программирование")

        self.hours_spin = QSpinBox()
        self.hours_spin.setRange(1, 9999)
        self.hours_spin.setValue(1)

        self.type_combo = QComboBox()
        self.type_combo.addItem("Выберите тип занятия", None)
        for lesson_type in LESSON_TYPES:
            self.type_combo.addItem(lesson_type_label(lesson_type), lesson_type)

        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setPlaceholderText("Дополнительные примечания")

        form.addRow("Номер занятия", self.number_spin)
        form.addRow("Дата", self.date_edit)
        form.addRow("Тема", self.topic_edit)
        form.addRow("Часы", self.hours_spin)
        form.addRow("Тип занятия", self.type_combo)
        form.addRow("Примечания", self.notes_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self, lesson: Lesson) -> None:
        self.number_spin.setValue(lesson.lesson_number)
        self.date_edit.setDate(
            QDate(lesson.date.year, lesson.date.month, lesson.date.day)
        )
        self.topic_edit.setText(lesson.topic)
        self.hours_spin.setValue(lesson.hours)
        index = self.type_combo.findData(lesson.lesson_type)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
        self.notes_edit.setPlainText(lesson.notes or "")

    def _on_save(self) -> None:
        try:
            if self._lesson is None:
                add_lesson(
                    self._session,
                    self._curriculum_subject.id,
                    self.number_spin.value(),
                    self.date_edit.date().toPython(),
                    self.topic_edit.text(),
                    self.hours_spin.value(),
                    self.type_combo.currentData(),
                    self.notes_edit.toPlainText(),
                )
            else:
                update_lesson(
                    self._session,
                    self._lesson,
                    self.number_spin.value(),
                    self.date_edit.date().toPython(),
                    self.topic_edit.text(),
                    self.hours_spin.value(),
                    self.type_combo.currentData(),
                    self.notes_edit.toPlainText(),
                )
        except LessonError as error:
            QMessageBox.warning(self, "Некорректные данные", str(error))
            return

        self.accept()
