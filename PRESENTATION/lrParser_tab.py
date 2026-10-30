from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QFileDialog, QMessageBox, QTabWidget, QGroupBox,
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

# Carpetas candidatas para abrir el diálogo por defecto
_FOLDER_CANDIDATES = [
    ROOT / "EXAMPLES" / "lr_parser",
    ROOT / "EXAMPLES" / "lr_parcer",
    ROOT / "EXAMPLES",
]

# Convención de sufijos para el auto-pareo
GRAMMAR_SUFFIXES = (".gram.txt", ".grammar.txt", ".gram", ".txt")
TOKEN_SUFFIXES = (
    ".tokens.txt", "_tokens.txt", ".tok.txt",
    ".terminals.txt", ".tira.txt",
)


def _find_stem(name, suffixes):
    """Devuelve el nombre sin el sufijo, o None si no coincide."""
    lower = name.lower()
    for suffix in suffixes:
        if lower.endswith(suffix):
            return name[: -len(suffix)]
    return None


def _is_token_file(path: Path) -> bool:
    return _find_stem(path.name, TOKEN_SUFFIXES) is not None


def _candidates_grammar(token_path: Path):
    """Dado un archivo de tokens, gramáticas pareja en la misma carpeta."""
    stem = _find_stem(token_path.name, TOKEN_SUFFIXES)
    if stem is None:
        return []
    folder = token_path.parent
    return [
        folder / (stem + suf)
        for suf in GRAMMAR_SUFFIXES
        if (folder / (stem + suf)).exists()
    ]


def _candidates_tokens(grammar_path: Path):
    """Dado un archivo de gramática, tokens pareja en la misma carpeta."""
    stem = _find_stem(grammar_path.name, GRAMMAR_SUFFIXES)
    if stem is None:
        stem = grammar_path.stem
    folder = grammar_path.parent
    return [
        folder / (stem + suf)
        for suf in TOKEN_SUFFIXES
        if (folder / (stem + suf)).exists()
    ]


def _default_folder() -> Path:
    for folder in _FOLDER_CANDIDATES:
        if folder.exists():
            return folder
    return ROOT / "EXAMPLES"


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
        self.grammar_path = None
        self.tokens_path = None
        self.source_path = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)

        title = QLabel("Analizador sintáctico LR")
        title.setObjectName("heading")
        layout.addWidget(title)

        hint = QLabel(
            "Carga un caso de prueba: la aplicación auto-empareja la "
            "gramática y la tira de tokens por nombre de archivo "
            "(ej. Prueba1.grammar.txt ↔ Prueba1.tokens.txt). Después elige "
            "la entrada (programa Pascal o tira de tokens) y analiza."
        )
        hint.setObjectName("subheading")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # ---------- Caso de prueba (par de archivos) ----------
        pair_group = QGroupBox("Caso de prueba")
        pair_layout = QVBoxLayout(pair_group)

        self.grammar_status = QLabel("Gramática: (sin cargar)")
        self.grammar_status.setWordWrap(True)
        pair_layout.addWidget(self.grammar_status)

        self.tokens_status = QLabel("Tira de tokens: (sin cargar)")
        self.tokens_status.setWordWrap(True)
        pair_layout.addWidget(self.tokens_status)

        pair_buttons = QHBoxLayout()
        self.load_pair_button = QPushButton("Cargar Gramatica y L.Tokens")
        self.load_pair_button.setToolTip(
            "Elige gramática o tokens. Si existe el par "
            "(mismo nombre + sufijo), se carga automáticamente."
        )
        self.load_pair_button.clicked.connect(self.load_any)
        pair_buttons.addWidget(self.load_pair_button)

        # self.load_grammar_button = QPushButton("Solo gramática")
        # self.load_grammar_button.clicked.connect(self.load_grammar_only)
        # pair_buttons.addWidget(self.load_grammar_button)

        # self.load_tokens_button = QPushButton("Solo tokens")
        # self.load_tokens_button.clicked.connect(self.load_tokens_only)
        # pair_buttons.addWidget(self.load_tokens_button)

        self.clear_pair_button = QPushButton("Limpiar")
        self.clear_pair_button.setObjectName("secondary")
        self.clear_pair_button.clicked.connect(self.clear_pair)
        pair_buttons.addWidget(self.clear_pair_button)
        pair_buttons.addStretch()
        pair_layout.addLayout(pair_buttons)
        layout.addWidget(pair_group)

        # ---------- Vista previa de la gramática ----------
        self.grammar_preview = QPlainTextEdit()
        self.grammar_preview.setReadOnly(True)
        self.grammar_preview.setMaximumHeight(150)
        layout.addWidget(self.grammar_preview)

        # ---------- Entrada ----------
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

        # Tab Tokens -------------------------------------------------
        tokens_widget = QWidget()
        tokens_layout = QVBoxLayout(tokens_widget)
        tokens_layout.setContentsMargins(8, 8, 8, 8)

        tokens_controls = QHBoxLayout()
        self.open_tokens_button = QPushButton("Abrir tira de tokens")
        self.open_tokens_button.clicked.connect(self.load_tokens_only)
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

        # ---------- Analizar ----------
        self.analyze_button = QPushButton("Analizar sintácticamente")
        self.analyze_button.setEnabled(False)
        self.analyze_button.clicked.connect(self.analyze)
        layout.addWidget(self.analyze_button)

        self.status = QLabel("Carga un caso de prueba para comenzar.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    # Estado

    @property
    def busy(self):
        return self.task is not None

    # Carga de archivos (par / individuales)

    def load_any(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar gramática o tira de tokens",
            str(_default_folder()),
            "Texto (*.txt);;Todos (*)",
        )
        if not path:
            return
        path = Path(path)
        if _is_token_file(path):
            if self._load_tokens_file(path):
                self._try_load_grammar_pair(path)
        else:
            if self._load_grammar_file(path):
                self._try_load_tokens_pair(path)

    def load_grammar_only(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir gramática", str(_default_folder()),
            "Texto (*.txt);;Todos (*)",
        )
        if not path:
            return
        path = Path(path)
        if self._load_grammar_file(path):
            self._try_load_tokens_pair(path)

    def load_tokens_only(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir tira de tokens", str(_default_folder()),
            "Texto (*.txt);;Todos (*)",
        )
        if not path:
            return
        path = Path(path)
        if _is_token_file(path) or self.grammar is None:
            if self._load_tokens_file(path):
                self._try_load_grammar_pair(path)
        else:
            # El usuario eligió una gramática por accidente: cargar como par
            if self._load_grammar_file(path):
                self._try_load_tokens_pair(path)

    def clear_pair(self):
        self.grammar = None
        self.table = None
        self.first = None
        self.follow = None
        self.collection = None
        self.grammar_path = None
        self.tokens_path = None
        self.grammar_preview.clear()
        self.tokens_editor.clear()
        self.grammar_status.setText("Gramática: (sin cargar)")
        self.tokens_status.setText("Tira de tokens: (sin cargar)")
        self.analyze_button.setEnabled(False)
        self.status.setText("Caso limpiado.")
        if self.results_window is not None:
            self.results_window.close()
            self.results_window = None

    # ---------- Gramática ----------

    def _load_grammar_file(self, path: Path) -> bool:
        path = Path(path)
        try:
            grammar = GrammarReader(path).read()
        except (OSError, ValueError) as error:
            self.status.setText(str(error))
            QMessageBox.warning(self, "Gramática inválida", str(error))
            return False

        self.grammar = grammar
        self.grammar_path = path
        self.grammar_status.setText(
            f"✓ Gramática: {path.name}  ·  {path.parent}"
        )
        self._show_grammar_preview(grammar)
        self._build_table()
        return True

    def _show_grammar_preview(self, grammar):
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

    def _try_load_tokens_pair(self, grammar_path: Path):
        candidates = _candidates_tokens(grammar_path)
        if candidates:
            pair = candidates[0]
            if self._load_tokens_file(pair):
                self.status.setText(
                    f"Par cargado: {grammar_path.name} ↔ {pair.name}"
                )
                return
        self.status.setText(
            f"Gramática cargada: {grammar_path.name}. "
            f"No se encontró tira de tokens pareja "
            f"({grammar_path.stem}.tokens.txt)."
        )

    # ---------- Tira de tokens ----------

    def _load_tokens_file(self, path: Path) -> bool:
        path = Path(path)
        try:
            text = read_text(path)
        except (OSError, UnicodeError) as error:
            QMessageBox.warning(self, "No se pudo leer", str(error))
            return False
        self.tokens_editor.setPlainText(text)
        self.tokens_path = path
        self.tokens_status.setText(
            f"✓ Tira de tokens: {path.name}  ·  {path.parent}"
        )
        self.input_tabs.setCurrentIndex(1)
        return True

    def _try_load_grammar_pair(self, token_path: Path):
        if self.grammar is not None and self.table is not None:
            self.status.setText(
                f"Tira de tokens cargada: {token_path.name}. "
                f"Gramática ya presente: {self.grammar_path.name}."
            )
            return
        candidates = _candidates_grammar(token_path)
        if candidates:
            pair = candidates[0]
            if self._load_grammar_file(pair):
                self.status.setText(
                    f"Par cargado: {pair.name} ↔ {token_path.name}"
                )
                return
        self.status.setText(
            f"Tira de tokens cargada: {token_path.name}. "
            f"No se encontró gramática pareja."
        )

    # ---------- Pascal suelto ----------

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

    # Construcción de la tabla

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
                f"Tabla lista con {len(self.table.conflicts)} conflicto(s). "
                "La gramática NO es SLR(1); revisa la pestaña Conflictos."
            )
        else:
            self.status.setText(
                "Tabla LR lista (SLR(1), sin conflictos). "
                "Elige entrada y pulsa Analizar."
            )

    def _on_table_error(self, message):
        self.table = None
        self.analyze_button.setEnabled(False)
        self.status.setText(message)
        QMessageBox.warning(self, "No se pudo construir la tabla", message)

    # Análisis

    def analyze(self):
        if self.grammar is None or self.table is None:
            self.status.setText("Primero carga un caso de prueba.")
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
                self.status.setText("Carga o escribe una tira de tokens.")
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
                f"{len(unmapped)} token(s) sin terminal equivalente "
                f"({sample}{'…' if len(unmapped) > 5 else ''})."
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
        unknown = [t for t, _ in mapped[:-1] if t not in valid]
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
        self.load_pair_button.setEnabled(not busy)
        # self.load_grammar_button.setEnabled(not busy)
        # self.load_tokens_button.setEnabled(not busy)
        self.clear_pair_button.setEnabled(not busy)
        self.open_pascal_button.setEnabled(not busy)
        self.open_tokens_button.setEnabled(not busy)
        self.analyze_button.setEnabled(
            not busy and self.table is not None
        )