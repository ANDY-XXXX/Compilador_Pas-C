"""Ventana independiente (top-level) y maximizable para mostrar resultados."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel,
    QPushButton, QHBoxLayout,
)

from .common import ResultsView
from .style import STYLE


class ResultsWindow(QMainWindow):
    def __init__(self, title, results, subtitle=None):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
            | Qt.WindowType.WindowMaximizeButtonHint
        )
        self.setWindowTitle(title)
        self.resize(1080, 720)
        self.setStyleSheet(STYLE)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        self.subtitle_label = QLabel(subtitle or "")
        self.subtitle_label.setObjectName("subheading")
        self.subtitle_label.setWordWrap(True)
        if not subtitle:
            self.subtitle_label.hide()
        layout.addWidget(self.subtitle_label)

        self.results_view = ResultsView()
        self.results_view.set_results(results)
        layout.addWidget(self.results_view, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        close_button = QPushButton("Cerrar ventana")
        close_button.setObjectName("secondary")
        close_button.clicked.connect(self.close)
        actions.addWidget(close_button)
        layout.addLayout(actions)

        self.setCentralWidget(central)

    def update_results(self, results, subtitle=None):
        self.results_view.set_results(results)
        if subtitle:
            self.subtitle_label.setText(subtitle)
            self.subtitle_label.show()