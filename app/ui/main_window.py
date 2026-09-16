from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.ui.pages import CurriculaPage, LessonPlanningPage, SubjectsPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Учебный планировщик")
        self.resize(1000, 640)

        self._build_ui()

    def _build_ui(self) -> None:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setFixedWidth(220)

        self.pages = QStackedWidget()

        self._add_section("Предметы", SubjectsPage())
        self._add_section("Учебные планы", CurriculaPage())
        self._add_section("Планирование занятий", LessonPlanningPage())

        self.navigation.currentRowChanged.connect(self._on_section_changed)
        self.navigation.setCurrentRow(0)

        layout.addWidget(self.navigation)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(container)

        self.statusBar().showMessage("Готово")

    def _add_section(self, title: str, page: QWidget) -> None:
        self.navigation.addItem(QListWidgetItem(title))
        self.pages.addWidget(page)

    def _on_section_changed(self, index: int) -> None:
        if index < 0:
            return
        self.pages.setCurrentIndex(index)
        self.statusBar().showMessage(self.navigation.item(index).text())
