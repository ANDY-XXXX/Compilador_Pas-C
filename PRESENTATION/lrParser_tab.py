from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QFileDialog, QMessageBox, QTabWidget,
)

from PERSISTENCE.grammar_reader import GrammarReader
from PERSISTENCE.text_files import read_text
from LOGIC.canonical_collection import Canonical_Collection
from LOGIC.first_follow import calculate_sets, calculate_first
from LOGIC.syntactic_analysis import (
    LRTable, LRParser, tokens_to_terminals,
)
from LOGIC.python_lexer.analyzer import analyze_code
from .common import Task
from .results_window import ResultsWindow


ROOT = Path(__file__).resolve().parents[1]


class LRParserTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grammar = None
        self.table = None
        self.first = None
        self.follow = None
        self.collection = None
        self.task = None
        self.results_window = None
        self.source_path = None
        self.tokens_path = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        title = QLabel("Analizador sintáctico LR")
        title.setObjectName("heading")
        layout.addWidget(title)

        hint = QLabel(
            "1) Carga la gramática → se construye la tabla LR. "
            "2) Carga un programa Pascal (se ejecuta el lexer) o una tira "
            "de tokens ya preparada. 3) Pulsa 'Analizar sintácticamente'."
        )
        hint.setObjectName("subheading")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # ---- Gramática ----
        self.load_grammar_button = QPushButton(
            "Cargar gramática y construir tabla"
        )
        self.load_grammar_button.clicked.connect(self.load_grammar)
        layout.addWidget(self.load_grammar_button)

        self.grammar_preview = QPlainTextEdit()
        self.grammar_preview.setReadOnly(True)
        self.grammar_preview.setMaximumHeight(150)
        layout.addWidget(self.grammar_preview)

        # ---- Entrada ----
        self.input_tabs = QTabWidget()

        # Tab Pascal
        pascal_widget = QWidget()
        pascal_layout = QVBoxLayout(pascal_widget)
        pascal_layout.setContentsMargins(8, 8, 8, 8)

        pascal_controls = QHBoxLayout()
        self.open_pascal_button = QPushButton("Abrir Pascal")
        self.open_pascal_button.clicked.connect(self.open_pascal)
        pascal_controls.addWidget(self.open_pascal_button)
        pascal_controls.addStretch()
        pascal_layout.addLayout(pascal_controls)

        self.pascal_editor = QPlainTextEdit()
        self.pascal_editor.setFont(QFont("Monospace", 11))
        self.pascal_editor.setPlaceholderText(
            "program Demo;\nvar x: integer;\nbegin\n  x := 1 + 2;\nend."
        )
        pascal_layout.addWidget(self.pascal_editor, 1)
        self.input_tabs.addTab(pascal_widget, "Programa Pascal")

        # Tab tokens
        tokens_widget = QWidget()
        tokens_layout = QVBoxLayout(tokens_widget)
        tokens_layout.setContentsMargins(8, 8, 8, 8)

        tokens_controls = QHBoxLayout()
        self.open_tokens_button = QPushButton("Abrir tokens")
        self.open_tokens_button.clicked.connect(self.open_tokens)
        tokens_controls.addWidget(self.open_tokens_button)
        tokens_controls.addStretch()
        tokens_layout.addLayout(tokens_controls)

        self.tokens_editor = QPlainTextEdit()
        self.tokens_editor.setFont(QFont("Monospace", 11))
        self.tokens_editor.setPlaceholderText(
            "Un terminal por línea o separados por espacios:\n"
            "id + id * id"
        )
        tokens_layout.addWidget(self.tokens_editor, 1)
        self.input_tabs.addTab(tokens_widget, "Tira de tokens")

        layout.addWidget(self.input_tabs, 1)

        # ---- Analizar ----
        self.analyze_button = QPushButton("Analizar sintácticamente")
        self.analyze_button.setEnabled(False)
        self.analyze_button.clicked.connect(self.analyze)
        layout.addWidget(self.analyze_button)

        self.status = QLabel("Carga una gramática para comenzar.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    # ---------- Estado ----------

    @property
    def busy(self):
        return self.task is not None

    # ---------- Gramática ----------

    def load_grammar(self):
        folder = ROOT / "EXAMPLES" / "canonical_collection"
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir gramática", str(folder),
            "Texto (*.txt);;Todos (*)",
        )
        if not path:
            return
        try:
            self.set_grammar(GrammarReader(path).read())
            self._build_table()
        except (OSError, ValueError) as error:
            self.grammar = None
            self.table = None
            self.grammar_preview.clear()
            self.analyze_button.setEnabled(False)
            self.status.setText(str(error))
            QMessageBox.warning(self, "Gramática inválida", str(error))

    def set_grammar(self, grammar):
        self.grammar = grammar
        lines = [
            "No terminales: " + " ".join(
                sorted(map(str, grammar.not_terminals))
            ),
            "Terminales: " + " ".join(
                sorted(map(str, grammar.terminals))
            ),
            "Inicial: " + str(grammar.start_symbol),
            "",
            "Producciones:",
        ]
        for index, production in enumerate(grammar.productions, 1):
            right = " ".join(map(str, production.right)) or "ε"
            marker = "  (aumentada)" if index == 1 else ""
            lines.append(f"  {index}. {production.left} → {right}{marker}")
        self.grammar_preview.setPlainText("\n".join(lines))

    def _build_table(self):
        if self.grammar is None:
            return
        grammar = self.grammar
        self.status.setText("Construyendo tabla LR…")
        self.task = Task(lambda: self._compute_table(grammar), self)
        self.task.completed.connect(self._on_table_built)
        self.task.failed.connect(self._on_table_error)
        self.task.finished.connect(self._finish_task)
        self.task.start()

    @staticmethod
    def _compute_table(grammar):
        first, follow = calculate_sets(grammar, calculate_first)
        collection = Canonical_Collection(grammar)
        collection.canonical_collection()
        table = LRTable(grammar, collection, follow).build()
        return first, follow, collection, table

    def _on_table_built(self, payload):
        self.first, self.follow, self.collection, self.table = payload
        self.analyze_button.setEnabled(True)
        if self.table.conflicts:
            self.status.setText(
                f"Tabla construida con {len(self.table.conflicts)} "
                "conflicto(s). Revisa la pestaña 'Conflictos' tras analizar."
            )
        else:
            self.status.setText(
                "Tabla LR lista (SLR(1) sin conflictos). "
                "Carga un programa o tira de tokens y pulsa Analizar."
            )

    def _on_table_error(self, message):
        self.table = None
        self.status.setText(message)
        QMessageBox.warning(self, "No se pudo construir la tabla", message)

    # ---------- Entrada ----------

    def open_pascal(self):
        folder = ROOT / "EXAMPLES" / "pythonLexer"
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Pascal", str(folder),
            "Pascal (*.pas);;Todos (*)",
        )
        if not path:
            return
        try:
            text = read_text(path)
            self.pascal_editor.setPlainText(text)
            self.source_path = Path(path)
            self.input_tabs.setCurrentIndex(0)
            self.status.setText(f"Programa cargado: {path}")
        except (OSError, UnicodeError) as error:
            QMessageBox.warning(self, "No se pudo leer", str(error))

    def open_tokens(self):
        folder = ROOT / "EXAMPLES"
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir tokens", str(folder),
            "Texto (*.txt);;Todos (*)",
        )
        if not path:
            return
        try:
            text = read_text(path)
            self.tokens_editor.setPlainText(text)
            self.tokens_path = Path(path)
            self.input_tabs.setCurrentIndex(1)
            self.status.setText(f"Tokens cargados: {path}")
        except (OSError, UnicodeError) as error:
            QMessageBox.warning(self, "No se pudo leer", str(error))

    # ---------- Análisis ----------

    def analyze(self):
        if self.grammar is None or self.table is None:
            self.status.setText("Primero carga la gramática.")
            return
        if self.busy:
            return

        grammar = self.grammar
        table = self.table

        if self.input_tabs.currentIndex() == 0:
            code = self.pascal_editor.toPlainText()
            if not code.strip():
                self.status.setText(
                    "Abre o escribe un programa antes de analizar."
                )
                return
            self._set_busy(True)
            self.status.setText("Tokenizando y analizando…")
            self.task = Task(
                lambda: self._run_pascal(grammar, table, code), self
            )
        else:
            raw = self.tokens_editor.toPlainText()
            if not raw.strip():
                self.status.setText(
                    "Carga o escribe una tira de tokens."
                )
                return
            self._set_busy(True)
            self.status.setText("Analizando tira de tokens…")
            self.task = Task(
                lambda: self._run_tokens(grammar, table, raw), self
            )

        self.task.completed.connect(self.show_result)
        self.task.failed.connect(self.show_error)
        self.task.finished.connect(self._finish_task)
        self.task.start()

    @staticmethod
    def _run_pascal(grammar, table, code):
        lex_result = analyze_code(code)
        raw_tokens = [
            t for t in lex_result["tokens"] if t.type.name != "EOF"
        ]
        mapped = tokens_to_terminals(
            lex_result["tokens"], grammar.terminals
        )

        valid = {str(t) for t in grammar.terminals}
        unmapped = [
            (lex, term) for lex, term in mapped if term not in valid
        ]
        if unmapped:
            sample = ", ".join(
                f"'{lex}'→'{term}'" for lex, term in unmapped[:5]
            )
            raise ValueError(
                f"{len(unmapped)} token(s) sin terminal equivalente en "
                f"la gramática ({sample}{'…' if len(unmapped) > 5 else ''})."
            )

        parser = LRParser(table, mapped)
        result = parser.parse()

        token_rows = [["Línea", "Col", "Lexema", "Token", "Terminal"]]
        for token, (lex, term) in zip(raw_tokens, mapped):
            token_rows.append([
                token.line, token.column, token.value,
                token.type.name, term,
            ])

        return {
            "tokens": token_rows,
            "parse": result,
            "lexer_errors": lex_result["errors"],
        }

    @staticmethod
    def _run_tokens(grammar, table, raw):
        parts = raw.split()
        if not parts:
            raise ValueError("La tira de tokens está vacía.")

        mapped = [(t, t) for t in parts if t != "$"]
        mapped.append(("$", "$"))

        valid = {str(t) for t in grammar.terminals}
        unknown = [
            t for t, _ in mapped[:-1] if t not in valid
        ]
        if unknown:
            raise ValueError(
                "Los siguientes terminales no están declarados en la "
                f"gramática: {sorted(set(unknown))}"
            )

        parser = LRParser(table, mapped)
        result = parser.parse()

        token_rows = [["#", "Terminal"]]
        for i, (_, term) in enumerate(mapped, 1):
            token_rows.append([i, term])

        return {
            "tokens": token_rows,
            "parse": result,
            "lexer_errors": [],
        }

    def show_result(self, payload):
        parse_result = payload["parse"]

        results = {
            "Tira de tokens": payload["tokens"],
            "Paso a paso": parse_result.step_rows(),
            "Derivación": parse_result.derivation_rows(),
            "Árbol": parse_result.tree_rows(),
        }

        if self.table is not None:
            results["Tabla unificada"] = self.table.combined_rows()
            results["ACTION"] = self.table.action_rows()
            results["GOTO"] = self.table.goto_rows()
            if self.table.conflicts:
                results["Conflictos"] = self.table.conflict_rows()

        if payload["lexer_errors"]:
            error_rows = [["Línea", "Descripción"]]
            for e in payload["lexer_errors"]:
                error_rows.append([e["line"], e["description"]])
            results["Errores léxicos"] = error_rows

        if parse_result.accepted:
            subtitle = "Cadena ACEPTADA · Análisis sintáctico exitoso."
        else:
            subtitle = f"Cadena RECHAZADA · {parse_result.error}"

        self.status.setText(subtitle)
        self._show_results(
            "Analizador sintáctico LR · Equipo 6", results, subtitle,
        )

    def _show_results(self, title, results, subtitle=None):
        try:
            if (self.results_window is None
                    or not self.results_window.isVisible()):
                if self.results_window is not None:
                    self.results_window.deleteLater()
                self.results_window = ResultsWindow(
                    title, results, subtitle
                )
                self.results_window.show()
            else:
                self.results_window.update_results(results, subtitle)
            self.results_window.raise_()
            self.results_window.activateWindow()
        except Exception as error:
            import traceback
            QMessageBox.critical(
                self, "No se pudo abrir la ventana de resultados",
                f"{type(error).__name__}: {error}\n\n"
                f"{traceback.format_exc()}",
            )

    def show_error(self, message):
        self.status.setText(message)
        QMessageBox.warning(self, "No se pudo analizar", message)

    def _finish_task(self):
        self._set_busy(False)
        if self.task is not None:
            self.task.deleteLater()
            self.task = None

    def _set_busy(self, busy):
        self.load_grammar_button.setEnabled(not busy)
        self.open_pascal_button.setEnabled(not busy)
        self.open_tokens_button.setEnabled(not busy)
        self.analyze_button.setEnabled(
            not busy and self.table is not None
        )