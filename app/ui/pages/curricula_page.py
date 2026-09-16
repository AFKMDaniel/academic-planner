from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import Curriculum, CurriculumSubject
from app.services.curriculum_service import (
    CurriculumError,
    count_curriculum_subjects,
    delete_curriculum,
    get_curriculum,
    list_curricula,
)
from app.services.curriculum_subject_service import (
    CurriculumSubjectError,
    count_lessons,
    get_curriculum_subject,
    list_available_subjects,
    list_curriculum_subjects,
    remove_curriculum_subject,
)
from app.ui.dialogs import (
    CurriculumDialog,
    CurriculumSubjectDialog,
    PlannedHoursDialog,
)
from app.ui.pages.base_page import BasePage


class CurriculaPage(BasePage):
    def __init__(
        self,
        session: Session | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="Учебные планы",
            subtitle="Учебные планы для группы и учебного года с их предметами.",
            parent=parent,
        )

        self._session = session if session is not None else SessionLocal()

        self._build_ui()

    def _build_ui(self) -> None:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_curriculum_panel())
        splitter.addWidget(self._build_subject_panel())
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)

        layout.addWidget(splitter)
        self.add_content(body)

    def _build_curriculum_panel(self) -> QWidget:
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(8)

        panel_layout.addLayout(self._build_curriculum_toolbar())

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Учебный год", "Группа"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.table.doubleClicked.connect(self._edit_curriculum)
        self.table.itemSelectionChanged.connect(self._refresh_subjects)

        panel_layout.addWidget(self.table)
        return panel

    def _build_subject_panel(self) -> QWidget:
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(8)

        self.subjects_label = QLabel(
            "Выберите учебный план, чтобы увидеть его предметы."
        )
        self.subjects_label.setObjectName("pageSubtitle")
        self.subjects_label.setWordWrap(True)
        panel_layout.addWidget(self.subjects_label)

        panel_layout.addLayout(self._build_subject_toolbar())

        self.subjects_table = QTableWidget(0, 3)
        self.subjects_table.setHorizontalHeaderLabels(
            ["Название предмета", "Код предмета", "Плановые часы"]
        )
        self.subjects_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.subjects_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self.subjects_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.subjects_table.verticalHeader().setVisible(False)
        self.subjects_table.setAlternatingRowColors(True)

        subject_header = self.subjects_table.horizontalHeader()
        subject_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        subject_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        subject_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        self.subjects_table.doubleClicked.connect(self._edit_hours)

        panel_layout.addWidget(self.subjects_table)
        return panel

    def _build_curriculum_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()

        self.create_button = QPushButton("Создать")
        self.edit_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")

        self.create_button.clicked.connect(self._create_curriculum)
        self.edit_button.clicked.connect(self._edit_curriculum)
        self.delete_button.clicked.connect(self._delete_curriculum)

        toolbar.addWidget(self.create_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addStretch()
        return toolbar

    def _build_subject_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()

        self.add_subject_button = QPushButton("Добавить предмет")
        self.edit_hours_button = QPushButton("Изменить плановые часы")
        self.remove_subject_button = QPushButton("Убрать предмет")

        self.add_subject_button.clicked.connect(self._add_subject)
        self.edit_hours_button.clicked.connect(self._edit_hours)
        self.remove_subject_button.clicked.connect(self._remove_subject)

        toolbar.addWidget(self.add_subject_button)
        toolbar.addWidget(self.edit_hours_button)
        toolbar.addWidget(self.remove_subject_button)
        toolbar.addStretch()
        return toolbar

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        curricula = list_curricula(self._session)
        self.table.setRowCount(0)

        for curriculum in curricula:
            row = self.table.rowCount()
            self.table.insertRow(row)

            year_item = QTableWidgetItem(curriculum.academic_year)
            year_item.setData(Qt.ItemDataRole.UserRole, curriculum.id)
            self.table.setItem(row, 0, year_item)
            self.table.setItem(row, 1, QTableWidgetItem(curriculum.group_name))

        self._refresh_subjects()

    def _refresh_subjects(self) -> None:
        curriculum = self._selected_curriculum()
        self.subjects_table.setRowCount(0)

        if curriculum is None:
            self.subjects_label.setText(
                "Выберите учебный план, чтобы увидеть его предметы."
            )
            return

        self.subjects_label.setText(
            f"Предметы группы {curriculum.group_name} ({curriculum.academic_year})"
        )

        for curriculum_subject in list_curriculum_subjects(
            self._session, curriculum.id
        ):
            row = self.subjects_table.rowCount()
            self.subjects_table.insertRow(row)

            name_item = QTableWidgetItem(curriculum_subject.subject.name)
            name_item.setData(Qt.ItemDataRole.UserRole, curriculum_subject.id)
            self.subjects_table.setItem(row, 0, name_item)
            self.subjects_table.setItem(
                row, 1, QTableWidgetItem(curriculum_subject.subject.code)
            )

            hours_item = QTableWidgetItem(str(curriculum_subject.hours))
            hours_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.subjects_table.setItem(row, 2, hours_item)

    def _selected_curriculum(self) -> Curriculum | None:
        row = self.table.currentRow()
        if row < 0:
            return None

        item = self.table.item(row, 0)
        if item is None:
            return None

        curriculum_id = item.data(Qt.ItemDataRole.UserRole)
        return get_curriculum(self._session, curriculum_id)

    def _selected_curriculum_subject(self) -> CurriculumSubject | None:
        row = self.subjects_table.currentRow()
        if row < 0:
            return None

        item = self.subjects_table.item(row, 0)
        if item is None:
            return None

        curriculum_subject_id = item.data(Qt.ItemDataRole.UserRole)
        return get_curriculum_subject(self._session, curriculum_subject_id)

    def _create_curriculum(self) -> None:
        dialog = CurriculumDialog(self._session, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit_curriculum(self) -> None:
        curriculum = self._selected_curriculum()
        if curriculum is None:
            QMessageBox.information(
                self, "Учебный план не выбран", "Выберите учебный план для изменения."
            )
            return

        dialog = CurriculumDialog(self._session, curriculum, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete_curriculum(self) -> None:
        curriculum = self._selected_curriculum()
        if curriculum is None:
            QMessageBox.information(
                self, "Учебный план не выбран", "Выберите учебный план для удаления."
            )
            return

        subject_count = count_curriculum_subjects(self._session, curriculum.id)
        message = (
            f"Удалить учебный план «{curriculum.academic_year}» "
            f"({curriculum.group_name})?"
        )
        if subject_count:
            message += (
                f"\n\nТакже будет удалено связанных предметов: {subject_count}, "
                "и все их занятия."
            )

        answer = QMessageBox.question(
            self,
            "Удаление учебного плана",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_curriculum(self._session, curriculum)
        except CurriculumError as error:
            QMessageBox.warning(self, "Не удалось удалить учебный план", str(error))
            return

        self.refresh()

    def _add_subject(self) -> None:
        curriculum = self._selected_curriculum()
        if curriculum is None:
            QMessageBox.information(
                self, "Учебный план не выбран", "Сначала выберите учебный план."
            )
            return

        if not list_available_subjects(self._session, curriculum.id):
            QMessageBox.information(
                self,
                "Нет доступных предметов",
                "Все предметы уже включены в этот учебный план. Сначала создайте "
                "новый предмет на странице «Предметы».",
            )
            return

        dialog = CurriculumSubjectDialog(self._session, curriculum, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_subjects()

    def _edit_hours(self) -> None:
        curriculum_subject = self._selected_curriculum_subject()
        if curriculum_subject is None:
            QMessageBox.information(
                self,
                "Предмет не выбран",
                "Выберите предмет учебного плана для изменения.",
            )
            return

        dialog = PlannedHoursDialog(self._session, curriculum_subject, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._refresh_subjects()

    def _remove_subject(self) -> None:
        curriculum_subject = self._selected_curriculum_subject()
        if curriculum_subject is None:
            QMessageBox.information(
                self,
                "Предмет не выбран",
                "Выберите предмет учебного плана для удаления.",
            )
            return

        subject = curriculum_subject.subject
        lesson_count = count_lessons(self._session, curriculum_subject.id)
        message = (
            f"Убрать предмет «{subject.name}» ({subject.code}) из учебного плана?"
        )
        if lesson_count:
            message += (
                f"\n\nТакже будет удалено связанных занятий: {lesson_count}."
            )

        answer = QMessageBox.question(
            self,
            "Удаление предмета",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            remove_curriculum_subject(self._session, curriculum_subject)
        except CurriculumSubjectError as error:
            QMessageBox.warning(self, "Не удалось убрать предмет", str(error))
            return

        self._refresh_subjects()
