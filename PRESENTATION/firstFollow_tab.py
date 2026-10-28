from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QFileDialog, QMessageBox,
)

from PERSISTENCE.grammar_reader import GrammarReader
from LOGIC.first_follow import calculate_sets, calculate_first
from .common import Task
from .results_window import ResultsWindow


def _set_rows(sets):
    return [["No terminal", "Conjunto"]] + [
        [name, "{ " + "  ".join(sorted(values)) + " }"]
        for name, values in sorted(sets.items())
    ]


class FirstFollowTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grammar = None
        self.task = None
        self.results_window = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        title = QLabel("PRIMEROS y SIGUIENTES")
        title.setObjectName("heading")
        layout.addWidget(title)

        self.load_button = QPushButton("Cargar y validar gramática")
        self.load_button.clicked.connect(self.load_grammar)
        layout.addWidget(self.load_button)

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview, 1)

        self.calc_button = QPushButton("Calcular PRIMEROS y SIGUIENTES")
        self.calc_button.setEnabled(False)
        self.calc_button.clicked.connect(self.calculate)
        layout.addWidget(self.calc_button)

        self.status = QLabel("Carga una gramática para comenzar.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    @property
    def busy(self):
        return self.task is not None

    def load_grammar(self):
        folder = Path(__file__).resolve().parents[1] / "EXAMPLES" / "first_follow"
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir gramática", str(folder),
            "Texto (*.txt);;Todos (*)",
        )
        if not path:
            return
        try:
            self.set_grammar(GrammarReader(path).read())
        except (OSError, ValueError) as error:
            self.grammar = None
            self.preview.clear()
            self.calc_button.setEnabled(False)
            self.status.setText(str(error))
            QMessageBox.warning(self, "Gramática inválida", str(error))

    def set_grammar(self, grammar):
        self.grammar = grammar
        lines = [
            "No terminales: " + " ".join(sorted(map(str, grammar.not_terminals))),
            "Terminales: " + " ".join(sorted(map(str, grammar.terminals))),
            "Inicial: " + str(grammar.start_symbol),
            "",
            "Producciones:",
        ]
        for production in grammar.productions:
            right = " ".join(map(str, production.right)) or "ε"
            lines.append(f"{production.left} → {right}")
        self.preview.setPlainText("\n".join(lines))
        self.calc_button.setEnabled(True)
        self.status.setText("Gramática válida. Lista para calcular.")

    def calculate(self):
        if self.grammar is None or self.busy:
            return
        grammar = self.grammar
        self._set_busy(True)
        self.status.setText("Calculando…")
        self.task = Task(
            lambda: calculate_sets(grammar, calculate_first), self
        )
        self.task.completed.connect(self.show_sets)
        self.task.failed.connect(self.show_error)
        self.task.finished.connect(self._finish_task)
        self.task.start()

    def show_sets(self, pair):
        first, follow = pair
        results = {
            "PRIMEROS": _set_rows(first),
            "SIGUIENTES": _set_rows(follow),
        }
        self.status.setText("Conjuntos calculados.")
        self._show_results(
            "PRIMEROS y SIGUIENTES", results,
            "Conjuntos calculados a partir de la gramática cargada.",
        )

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

    def show_error(self, message):
        self.status.setText(message)
        QMessageBox.warning(self, "No se pudo calcular", message)

    def _finish_task(self):
        self._set_busy(False)
        if self.task is not None:
            self.task.deleteLater()
            self.task = None

    def _set_busy(self, busy):
        self.load_button.setEnabled(not busy)
        self.calc_button.setEnabled(not busy and self.grammar is not None)