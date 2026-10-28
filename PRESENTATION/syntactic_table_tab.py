from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QFileDialog, QMessageBox,
)

from PERSISTENCE.grammar_reader import GrammarReader
from LOGIC.canonical_collection import Canonical_Collection
from LOGIC.first_follow import calculate_sets, calculate_first
from LOGIC.syntactic_analysis import LRTable
from .common import Task
from .results_window import ResultsWindow


def _set_rows(sets):
    return [["No terminal", "Conjunto"]] + [
        [name, "{ " + "  ".join(sorted(values)) + " }"]
        for name, values in sorted(sets.items())
    ]


class SyntacticTableTab(QWidget):
    """Tabla SLR(1) con la cadena de cálculo completa."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grammar = None
        self.task = None
        self.results_window = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        title = QLabel("Tabla de análisis sintáctico LR")
        title.setObjectName("heading")
        layout.addWidget(title)

        hint = QLabel(
            "Se calcularán PRIMEROS, SIGUIENTES, la colección canónica "
            "y la tabla. Todos los pasos se mostrarán juntos en una ventana."
        )
        hint.setObjectName("subheading")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self.load_button = QPushButton("Cargar y validar gramática")
        self.load_button.clicked.connect(self.load_grammar)
        layout.addWidget(self.load_button)

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        layout.addWidget(self.preview, 1)

        self.calc_button = QPushButton("Construir tabla LR")
        self.calc_button.setEnabled(False)
        self.calc_button.clicked.connect(self.calculate)
        layout.addWidget(self.calc_button)

        self.status = QLabel("Carga una gramática aumentada para comenzar.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    @property
    def busy(self):
        return self.task is not None

    def load_grammar(self):
        folder = (
            Path(__file__).resolve().parents[1]
            / "EXAMPLES" / "canonical_collection"
        )
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
        for index, production in enumerate(grammar.productions, 1):
            right = " ".join(map(str, production.right)) or "ε"
            marker = "  (aumentada)" if index == 1 else ""
            lines.append(f"  {index}. {production.left} → {right}{marker}")
        self.preview.setPlainText("\n".join(lines))
        self.calc_button.setEnabled(True)
        self.status.setText("Gramática válida. Lista para construir la tabla.")

    def calculate(self):
        if self.grammar is None or self.busy:
            return
        grammar = self.grammar
        self._set_busy(True)
        self.status.setText(
            "Construyendo tabla (PRIMEROS → SIGUIENTES → colección → tabla)…"
        )
        self.task = Task(lambda: self._compute(grammar), self)
        self.task.completed.connect(self.show_table)
        self.task.failed.connect(self.show_error)
        self.task.finished.connect(self._finish_task)
        self.task.start()

    @staticmethod
    def _compute(grammar):
        first, follow = calculate_sets(grammar, calculate_first)
        collection = Canonical_Collection(grammar)
        collection.canonical_collection()
        table = LRTable(grammar, collection, follow).build()
        return first, follow, collection, table

    def show_table(self, payload):
        first, follow, collection, table = payload

        state_rows = [["Estado", "Ítem"]]
        for i, state in enumerate(collection.states):
            for item in state:
                state_rows.append([f"I{i}", str(item)])

        transition_rows = [["Origen", "Símbolo", "Destino", "Aceptación"]]
        for origin, symbol, target in collection.transitions:
            accepting = "Sí" if target in collection.acceptation else ""
            transition_rows.append([
                f"I{origin}", str(symbol), f"I{target}", accepting,
            ])

        results = {
            "PRIMEROS": _set_rows(first),
            "SIGUIENTES": _set_rows(follow),
            "Estados": state_rows,
            "Transiciones": transition_rows,
            "Tabla unificada": table.combined_rows(),
            "ACTION": table.action_rows(),
            "GOTO": table.goto_rows(),
        }
        if table.conflicts:
            results["Conflictos"] = table.conflict_rows()

        subtitle = (
            f"{len(collection.states)} estados · "
            f"{len(collection.transitions)} transiciones"
        )
        if table.conflicts:
            subtitle += (
                f" · {len(table.conflicts)} conflicto(s) "
                "— la gramática NO es SLR(1)"
            )
        else:
            subtitle += " · sin conflictos: gramática SLR(1)"

        self.status.setText(subtitle)
        self._show_results("Tabla de análisis LR · Equipo 6", results, subtitle)

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
        QMessageBox.warning(self, "No se pudo construir la tabla", message)

    def _finish_task(self):
        self._set_busy(False)
        if self.task is not None:
            self.task.deleteLater()
            self.task = None

    def _set_busy(self, busy):
        self.load_button.setEnabled(not busy)
        self.calc_button.setEnabled(not busy and self.grammar is not None)