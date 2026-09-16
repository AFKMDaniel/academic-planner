from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import CurriculumSubject, Lesson
from app.services.curriculum_service import list_curricula
from app.services.curriculum_subject_service import (
    allocated_lesson_hours,
    get_curriculum_subject,
    list_curriculum_subjects,
)
from app.services.lesson_service import LessonError, delete_lesson, list_lessons
from app.ui.dialogs import LessonDialog
from app.ui.lesson_types import lesson_type_label
from app.ui.pages.base_page import BasePage

class LessonPlanningPage(BasePage):
    def __init__(
        self,
        session: Session | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="Планирование занятий",
            subtitle="Календарно-тематическое планирование по предметам "
            "учебного плана.",
            parent=parent,
        )

        self._session = session if session is not None else SessionLocal()

        self._build_ui()

    def _build_ui(self) -> None:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addLayout(self._build_selectors())
        layout.addLayout(self._build_toolbar())
        layout.addWidget(self._build_summary())

        self.lessons_label = QLabel(
            "Выберите учебный план и предмет, чтобы увидеть занятия."
        )
        self.lessons_label.setObjectName("pageSubtitle")
        self.lessons_label.setWordWrap(True)
        layout.addWidget(self.lessons_label)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Номер занятия", "Дата", "Тема", "Часы", "Тип занятия", "Примечания"]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._edit_lesson)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.table)
        self.add_content(body)

    def _build_selectors(self) -> QFormLayout:
        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)

        self.curriculum_combo = QComboBox()
        self.curriculum_combo.currentIndexChanged.connect(self._on_curriculum_changed)

        self.subject_combo = QComboBox()
        self.subject_combo.currentIndexChanged.connect(self._on_subject_changed)

        form.addRow("Учебный план:", self.curriculum_combo)
        form.addRow("Предмет:", self.subject_combo)
        return form

    def _build_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()

        self.create_lesson_button = QPushButton("Создать занятие")
        self.create_lesson_button.clicked.connect(self._create_lesson)

        self.edit_lesson_button = QPushButton("Изменить занятие")
        self.edit_lesson_button.clicked.connect(self._edit_lesson)

        self.delete_lesson_button = QPushButton("Удалить занятие")
        self.delete_lesson_button.clicked.connect(self._delete_lesson)

        toolbar.addWidget(self.create_lesson_button)
        toolbar.addWidget(self.edit_lesson_button)
        toolbar.addWidget(self.delete_lesson_button)
        toolbar.addStretch()
        return toolbar

    def _build_summary(self) -> QWidget:
        summary = QWidget()
        summary.setObjectName("hoursSummary")
        layout = QHBoxLayout(summary)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(40)

        self.planned_hours_value = self._add_summary_item(layout, "Плановые часы")
        self.allocated_hours_value = self._add_summary_item(
            layout, "Распределено часов"
        )
        self.remaining_hours_value = self._add_summary_item(layout, "Остаток часов")

        layout.addStretch()
        return summary

    def _add_summary_item(self, layout: QHBoxLayout, caption: str) -> QLabel:
        item = QWidget()
        item_layout = QVBoxLayout(item)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(2)

        value_label = QLabel("—")
        value_label.setObjectName("summaryValue")

        caption_label = QLabel(caption)
        caption_label.setObjectName("summaryCaption")

        item_layout.addWidget(value_label)
        item_layout.addWidget(caption_label)
        layout.addWidget(item)
        return value_label

    def _update_hours_summary(
        self, curriculum_subject: CurriculumSubject | None
    ) -> None:
        if curriculum_subject is None:
            self.planned_hours_value.setText("—")
            self.allocated_hours_value.setText("—")
            self.remaining_hours_value.setText("—")
            return

        planned_hours = curriculum_subject.hours
        allocated_hours = allocated_lesson_hours(
            self._session, curriculum_subject.id
        )
        remaining_hours = planned_hours - allocated_hours

        self.planned_hours_value.setText(str(planned_hours))
        self.allocated_hours_value.setText(str(allocated_hours))
        self.remaining_hours_value.setText(str(remaining_hours))

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        self._populate_curricula()
        self._on_curriculum_changed()

    def _populate_curricula(self) -> None:
        self.curriculum_combo.blockSignals(True)
        self.curriculum_combo.clear()
        for curriculum in list_curricula(self._session):
            label = f"{curriculum.group_name} ({curriculum.academic_year})"
            self.curriculum_combo.addItem(label, curriculum.id)
        self.curriculum_combo.setCurrentIndex(-1)
        self.curriculum_combo.blockSignals(False)

    def _on_curriculum_changed(self) -> None:
        self._populate_subjects()
        self._on_subject_changed()

    def _populate_subjects(self) -> None:
        curriculum_id = self.curriculum_combo.currentData()

        self.subject_combo.blockSignals(True)
        self.subject_combo.clear()
        if curriculum_id is not None:
            for curriculum_subject in list_curriculum_subjects(
                self._session, curriculum_id
            ):
                self.subject_combo.addItem(
                    f"{curriculum_subject.subject.name} "
                    f"({curriculum_subject.subject.code})",
                    curriculum_subject.id,
                )
        self.subject_combo.setCurrentIndex(-1)
        self.subject_combo.blockSignals(False)

    def _on_subject_changed(self) -> None:
        self._load_lessons()

    def _create_lesson(self) -> None:
        curriculum_subject = self._selected_curriculum_subject()
        if curriculum_subject is None:
            QMessageBox.information(
                self,
                "Предмет не выбран",
                "Сначала выберите учебный план и предмет.",
            )
            return

        dialog = LessonDialog(self._session, curriculum_subject, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_lessons()

    def _edit_lesson(self) -> None:
        lesson = self._selected_lesson()
        if lesson is None:
            QMessageBox.information(
                self, "Занятие не выбрано", "Выберите занятие для изменения."
            )
            return

        curriculum_subject = get_curriculum_subject(
            self._session, lesson.curriculum_subject_id
        )
        if curriculum_subject is None:
            QMessageBox.warning(
                self,
                "Не удалось изменить занятие",
                "Предмет учебного плана для этого занятия больше недоступен.",
            )
            return

        dialog = LessonDialog(
            self._session, curriculum_subject, lesson, parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_lessons()

    def _delete_lesson(self) -> None:
        lesson = self._selected_lesson()
        if lesson is None:
            QMessageBox.information(
                self, "Занятие не выбрано", "Выберите занятие для удаления."
            )
            return

        answer = QMessageBox.question(
            self,
            "Удаление занятия",
            f"Удалить занятие №{lesson.lesson_number} «{lesson.topic}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_lesson(self._session, lesson)
        except LessonError as error:
            QMessageBox.warning(self, "Не удалось удалить занятие", str(error))
            return

        self._load_lessons()

    def _selected_curriculum_subject(self) -> CurriculumSubject | None:
        curriculum_subject_id = self.subject_combo.currentData()
        if curriculum_subject_id is None:
            return None
        return get_curriculum_subject(self._session, curriculum_subject_id)

    def _selected_lesson(self) -> Lesson | None:
        row = self.table.currentRow()
        if row < 0:
            return None

        item = self.table.item(row, 0)
        if item is None:
            return None

        lesson_id = item.data(Qt.ItemDataRole.UserRole)
        return self._session.get(Lesson, lesson_id)

    def _load_lessons(self) -> None:
        curriculum_subject_id = self.subject_combo.currentData()
        self.table.setRowCount(0)

        if curriculum_subject_id is None:
            self.lessons_label.setText(
                "Выберите учебный план и предмет, чтобы увидеть занятия."
            )
            self._update_hours_summary(None)
            return

        curriculum_subject = get_curriculum_subject(
            self._session, curriculum_subject_id
        )
        if curriculum_subject is None:
            self.lessons_label.setText(
                "Выбранный предмет больше недоступен."
            )
            self._update_hours_summary(None)
            return

        lessons = list_lessons(self._session, curriculum_subject_id)
        self.lessons_label.setText(
            f"Занятия по предмету {curriculum_subject.subject.name} "
            f"({curriculum_subject.subject.code})."
        )
        self._update_hours_summary(curriculum_subject)

        for lesson in lessons:
            row = self.table.rowCount()
            self.table.insertRow(row)

            number_item = QTableWidgetItem(str(lesson.lesson_number))
            number_item.setData(Qt.ItemDataRole.UserRole, lesson.id)
            number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, number_item)

            date_item = QTableWidgetItem(lesson.date.strftime("%d.%m.%Y"))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, date_item)

            self.table.setItem(row, 2, QTableWidgetItem(lesson.topic))

            hours_item = QTableWidgetItem(str(lesson.hours))
            hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, hours_item)

            self.table.setItem(row, 4, QTableWidgetItem(
                lesson_type_label(lesson.lesson_type)
            ))
            self.table.setItem(row, 5, QTableWidgetItem(lesson.notes or ""))
