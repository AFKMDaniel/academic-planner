import sys
import traceback
from types import TracebackType

from PySide6.QtWidgets import QApplication, QMessageBox


def install_exception_hook() -> None:
    """Route unhandled exceptions to a dialog instead of a traceback or crash."""
    sys.excepthook = _handle_exception


def _handle_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    traceback.print_exception(exc_type, exc_value, exc_traceback)

    if QApplication.instance() is None:
        return

    QMessageBox.critical(
        None,
        "Непредвиденная ошибка",
        "Произошла непредвиденная ошибка, действие не удалось завершить.\n\n"
        "Попробуйте ещё раз. Если проблема повторяется, перезапустите приложение.",
    )
