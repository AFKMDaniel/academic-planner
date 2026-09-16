from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class BasePage(QWidget):
    """Common layout shared by the top-level application sections."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(28, 24, 28, 24)
        self._layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        self._layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("pageSubtitle")
            subtitle_label.setWordWrap(True)
            self._layout.addWidget(subtitle_label)

        self._layout.addSpacing(12)
        self._layout.addStretch()

    def add_content(self, widget: QWidget) -> None:
        """Add a widget above the trailing stretch."""
        self._layout.insertWidget(self._layout.count() - 1, widget)
        self._layout.setStretchFactor(widget, 1)
