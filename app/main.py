import sys
import traceback
from pathlib import Path

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication, QMessageBox

from app.database.connection import SessionLocal
from app.database.init import init_database
from app.services.demo_data import seed_demo_data
from app.ui.error_handling import install_exception_hook
from app.ui.main_window import MainWindow

STYLE_PATH = Path(__file__).resolve().parents[1] / "resources" / "style.qss"


def load_stylesheet() -> str:
    if STYLE_PATH.exists():
        return STYLE_PATH.read_text(encoding="utf-8")
    return ""


def install_russian_translation(app: QApplication) -> None:
    translator = QTranslator(app)
    translations_path = QLibraryInfo.path(
        QLibraryInfo.LibraryPath.TranslationsPath
    )
    if translator.load(
        QLocale(QLocale.Language.Russian), "qtbase", "_", translations_path
    ):
        app.installTranslator(translator)


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Учебный планировщик")
    app.setStyleSheet(load_stylesheet())
    install_russian_translation(app)
    install_exception_hook()

    if not _prepare_database():
        return 1

    window = MainWindow()
    window.show()
    return app.exec()


def _prepare_database() -> bool:
    try:
        init_database()
        with SessionLocal() as session:
            seed_demo_data(session)
    except Exception:
        traceback.print_exc()
        QMessageBox.critical(
            None,
            "Ошибка базы данных",
            "Не удалось открыть базу данных приложения.\n\n"
            "Проверьте, что папка приложения доступна для записи, "
            "и попробуйте снова.",
        )
        return False
    return True


if __name__ == "__main__":
    sys.exit(main())
