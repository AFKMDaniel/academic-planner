from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from app.database.connection import SessionLocal
from app.models import Subject
from app.services.subject_service import (
    SubjectError,
    delete_subject,
    get_subject,
    list_subjects,
)
from app.ui.dialogs import SubjectDialog
from app.ui.pages.base_page import BasePage


class SubjectsPage(BasePage):
    def __init__(
        self,
        session: Session | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(
            title="Предметы",
            subtitle="Учебные предметы, доступные для учебных планов.",
            parent=parent,
        )

        self._session = session if session is not None else SessionLocal()

        self._build_ui()

    def _build_ui(self) -> None:
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addLayout(self._build_toolbar())

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Название", "Код"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self.table.doubleClicked.connect(self._edit_subject)

        layout.addWidget(self.table)
        self.add_content(body)

    def _build_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()

        self.create_button = QPushButton("Создать")
        self.edit_button = QPushButton("Изменить")
        self.delete_button = QPushButton("Удалить")

        self.create_button.clicked.connect(self._create_subject)
        self.edit_button.clicked.connect(self._edit_subject)
        self.delete_button.clicked.connect(self._delete_subject)

        toolbar.addWidget(self.create_button)
        toolbar.addWidget(self.edit_button)
        toolbar.addWidget(self.delete_button)
        toolbar.addStretch()
        return toolbar

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.refresh()

    def refresh(self) -> None:
        subjects = list_subjects(self._session)
        self.table.setRowCount(0)

        for subject in subjects:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(subject.name)
            name_item.setData(Qt.ItemDataRole.UserRole, subject.id)
            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, QTableWidgetItem(subject.code))

    def _selected_subject(self) -> Subject | None:
        row = self.table.currentRow()
        if row < 0:
            return None

        item = self.table.item(row, 0)
        if item is None:
            return None

        subject_id = item.data(Qt.ItemDataRole.UserRole)
        return get_subject(self._session, subject_id)

    def _create_subject(self) -> None:
        dialog = SubjectDialog(self._session, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _edit_subject(self) -> None:
        subject = self._selected_subject()
        if subject is None:
            QMessageBox.information(
                self, "Предмет не выбран", "Выберите предмет для изменения."
            )
            return

        dialog = SubjectDialog(self._session, subject, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh()

    def _delete_subject(self) -> None:
        subject = self._selected_subject()
        if subject is None:
            QMessageBox.information(
                self, "Предмет не выбран", "Выберите предмет для удаления."
            )
            return

        answer = QMessageBox.question(
            self,
            "Удаление предмета",
            f"Удалить предмет «{subject.name}» ({subject.code})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            delete_subject(self._session, subject)
        except SubjectError as error:
            QMessageBox.warning(self, "Не удалось удалить предмет", str(error))
            return

        self.refresh()
