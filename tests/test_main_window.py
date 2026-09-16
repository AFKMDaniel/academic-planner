import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def test_main_window_navigation_switches_pages():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.navigation.count() == 3
    assert window.pages.count() == 3

    window.navigation.setCurrentRow(2)
    assert window.pages.currentIndex() == 2

    window.navigation.setCurrentRow(1)
    assert window.pages.currentIndex() == 1

    window.navigation.setCurrentRow(0)
    assert window.pages.currentIndex() == 0
