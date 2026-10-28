from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QPlainTextEdit, QFileDialog, QMessageBox,
)

from PERSISTENCE.text_files import read_text, write_text
from .common import Task
from .results_window import ResultsWindow

ROOT = Path(__file__).resolve().parents[1]


class LexerTabBase(QWidget):
    """Base para pestañas de análisis léxico.

    Los resultados se muestran en una ventana independiente (ResultsWindow).
    """

    def __init__(self, title, example_folder, parent=None):
        super().__init__(parent)
        self.example_folder = ROOT / "EXAMPLES" / example_folder
        self.task = None
        self.path = None
        self.results_window = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 18, 24, 18)
        self.layout.setSpacing(12)

        heading = QLabel(title)
        heading.setObjectName("heading")
        self.layout.addWidget(heading)

        self.controls = QHBoxLayout()
        self.open_button = QPushButton("Abrir Pascal")
        self.save_button = QPushButton("Guardar como…")
        self.analyze_button = QPushButton("Analizar")
        self.clear_button = QPushButton("Limpiar")
        self.buttons = [
            self.open_button, self.save_button,
            self.analyze_button, self.clear_button,
        ]
        for button in self.buttons:
            self.controls.addWidget(button)
        self.controls.addStretch()
        self.layout.addLayout(self.controls)

        self.path_label = QLabel("Escribe código o abre un archivo .pas.")
        self.path_label.setWordWrap(True)
        self.layout.addWidget(self.path_label)

        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "program Ejemplo;\nvar x: integer;\nbegin\n  x := 1;\nend."
        )
        self.editor.setFont(QFont("Monospace", 11))
        self.layout.addWidget(self.editor, 1)

        self.status = QLabel("Listo.")
        self.status.setWordWrap(True)
        self.layout.addWidget(self.status)

        self.open_button.clicked.connect(self.open_source)
        self.save_button.clicked.connect(self.save_source)
        self.analyze_button.clicked.connect(self.analyze)
        self.clear_button.clicked.connect(self.clear)
        self.editor.textChanged.connect(self.invalidate_results)

    # ---------------- Estado ----------------

    @property
    def busy(self):
        return self.task is not None

    def invalidate_results(self):
        self.status.setText(
            "Texto modificado. Ejecuta el análisis para actualizar los resultados."
        )

    # ---------------- Ventana de resultados ----------------

    def _show_results(self, title, results, subtitle=None):
        try:
            if (self.results_window is None
                    or not self.results_window.isVisible()):
                if self.results_window is not None:
                    self.results_window.deleteLater()
                self.results_window = ResultsWindow(title, results, subtitle)
                self.results_window.show()
            else:
                self.results_window.update_results(results, subtitle)
            self.results_window.raise_()
            self.results_window.activateWindow()
        except Exception as error:
            import traceback
            QMessageBox.critical(
                self, "No se pudo abrir la ventana de resultados",
                f"{type(error).__name__}: {error}\n\n{traceback.format_exc()}",
            )

    # ---------------- Archivos ----------------

    def clear(self):
        self.editor.blockSignals(True)
        self.editor.clear()
        self.editor.blockSignals(False)
        self.path = None
        self.path_label.setText("Nuevo código.")
        self.status.setText("Listo.")
        if self.results_window is not None:
            self.results_window.close()
            self.results_window = None

    def open_source(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Pascal", str(self.example_folder),
            "Pascal (*.pas);;Todos (*)",
        )
        if not path:
            return
        try:
            text = read_text(path)
            self.editor.setPlainText(text)
            self.path = Path(path)
            self.path_label.setText(str(self.path))
        except (OSError, UnicodeError) as error:
            self.show_error(str(error))

    def save_source(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar copia", str(self.path or "programa.pas"),
            "Pascal (*.pas)",
        )
        if not path:
            return
        try:
            write_text(path, self.editor.toPlainText())
            self.path = Path(path)
            self.path_label.setText(str(self.path))
        except OSError as error:
            self.show_error(str(error))

    # ---------------- Tareas ----------------

    def start_task(self, function, on_success, message):
        if self.busy:
            return
        self.status.setText(message)
        for button in self.buttons:
            button.setEnabled(False)
        self.editor.setReadOnly(True)

        self.task = Task(function, self)
        self.task.completed.connect(on_success)
        self.task.failed.connect(self.show_error)
        self.task.finished.connect(self._finish_task)
        self.task.start()

    def _finish_task(self):
        task = self.task
        self.task = None
        for button in self.buttons:
            button.setEnabled(True)
        self.editor.setReadOnly(False)
        if task is not None:
            task.deleteLater()

    def show_error(self, message):
        self.status.setText(message)
        QMessageBox.warning(self, "No se pudo completar la operación", message)

    def analyze(self):
        raise NotImplementedError