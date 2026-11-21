from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QFileDialog, QMessageBox, QSplitter, QGridLayout,
    QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt

from PERSISTENCE.semantic_grammar_reader import SemanticGrammarReader
from PERSISTENCE.text_files import read_text
from LOGIC.canonical_collection import Canonical_Collection
from LOGIC.first_follow import calculate_sets, calculate_first
from LOGIC.syntactic_analysis import LRTable
from LOGIC.semantic_analysis.semantic_parser import SemanticParser
from LOGIC.python_lexer.analyzer import analyze_code
from LOGIC.syntactic_analysis.terminal_mapping import tokens_to_terminals
from .common import Task
from .results_window import ResultsWindow
from .line_numbered_editor import LineNumberedEditor

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "EXAMPLES" / "semantic"


def _set_rows(sets):
    return [["No terminal", "Conjunto"]] + [
        [name, "{ " + "  ".join(sorted(values)) + " }"]
        for name, values in sorted(sets.items())
    ]


def _grammar_lines(grammar):
    return [f"{i + 1}. {prod}" for i, prod in enumerate(grammar.productions)]


def _action_lines(grammar):
    actions = getattr(grammar, "actions", {})
    return [
        f"{i + 1}. {{ {actions[i]} }}" if i in actions else f"{i + 1}. (sin acción)"
        for i in range(len(grammar.productions))
    ]


def _source_candidates(grammar_path):
    """Busca el código fuente pareja: Prueba1.grammar.txt -> Prueba1.ProFuente.txt"""
    # Limpiamos el nombre para obtener solo el prefijo (ej. "Prueba1")
    stem = grammar_path.name.replace(".grammar.txt", "").replace(".sem.txt", "").replace(".txt", "")
    return sorted(
        p for p in grammar_path.parent.glob(f"{stem}*")
        if not p.name.endswith(".grammar.txt") and not p.name.endswith(".sem.txt") and p.suffix in (".txt", ".pas")
    )


class SemanticTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grammar = None
        self.grammar_text = ""
        self.grammar_path = None
        self.source_path = None
        self.table = None
        self.first = None
        self.follow = None
        self.collection = None
        self.task = None
        self.results_window = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)

        title = QLabel("Analizador Semántico LR (Acciones)")
        title.setObjectName("heading")
        layout.addWidget(title)

        # ==========================================================
        # NUEVO: Acceso rápido a pruebas (ComboBox)
        # ==========================================================
        test_group = QGroupBox("Acceso rápido a pruebas")
        test_layout = QHBoxLayout(test_group)
        
        self.test_combo = QComboBox()
        self.test_combo.setMinimumWidth(300)
        self.test_combo.currentIndexChanged.connect(self._on_test_selected)
        
        self.btn_refresh = QPushButton("Actualizar lista")
        self.btn_refresh.setObjectName("secondary")
        self.btn_refresh.clicked.connect(self._refresh_test_cases)
        
        test_layout.addWidget(QLabel("Selecciona un caso:"))
        test_layout.addWidget(self.test_combo, 1)
        test_layout.addWidget(self.btn_refresh)
        layout.addWidget(test_group)
        
        # Llenar el combo al iniciar
        self._refresh_test_cases()
        # ==========================================================

        # --- Selección manual de archivos ---
        files = QGridLayout()
        self.btn_load_grammar = QPushButton("Abrir otra gramática")
        self.btn_load_grammar.clicked.connect(self.load_grammar)
        self.grammar_label = QLabel("Ninguna gramática seleccionada")
        self.grammar_label.setObjectName("subheading")
        files.addWidget(QLabel("Gramática:"), 0, 0)
        files.addWidget(self.btn_load_grammar, 0, 1)
        files.addWidget(self.grammar_label, 0, 2)

        self.btn_load_source = QPushButton("Abrir otro código")
        self.btn_load_source.clicked.connect(self.load_source)
        self.source_label = QLabel("Ningún código seleccionado (también puedes escribirlo)")
        self.source_label.setObjectName("subheading")
        files.addWidget(QLabel("Código fuente:"), 1, 0)
        files.addWidget(self.btn_load_source, 1, 1)
        files.addWidget(self.source_label, 1, 2)
        files.setColumnStretch(2, 1)
        layout.addLayout(files)

        controls = QHBoxLayout()
        self.btn_analyze = QPushButton("Ejecutar Análisis Semántico")
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.clicked.connect(self.analyze)
        controls.addWidget(self.btn_analyze)

        self.btn_clear_run = QPushButton("Limpiar corrida")
        self.btn_clear_run.setObjectName("secondary")
        self.btn_clear_run.clicked.connect(self.clear_run)
        controls.addWidget(self.btn_clear_run)

        self.btn_clear_all = QPushButton("Limpiar todo")
        self.btn_clear_all.setObjectName("secondary")
        self.btn_clear_all.clicked.connect(self.clear_all)
        controls.addWidget(self.btn_clear_all)
        controls.addStretch()
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.grammar_view = QPlainTextEdit()
        self.grammar_view.setReadOnly(True)
        self.grammar_view.setPlaceholderText("Gramática (producciones numeradas)...")
        splitter.addWidget(self._panel("Gramática", self.grammar_view))

        self.actions_view = QPlainTextEdit()
        self.actions_view.setReadOnly(True)
        self.actions_view.setPlaceholderText("Acciones semánticas de cada producción...")
        splitter.addWidget(self._panel("Acciones semánticas", self.actions_view))

        self.source_view = LineNumberedEditor()
        self.source_view.setPlaceholderText("Programa fuente (ej. 2 + 3 * 4)...")
        splitter.addWidget(self._panel("Programa fuente", self.source_view))

        layout.addWidget(splitter, 1)

        self.status = QLabel("Carga una gramática semántica para comenzar.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    @staticmethod
    def _panel(title, widget):
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        label = QLabel(title)
        label.setObjectName("subheading")
        panel_layout.addWidget(label)
        panel_layout.addWidget(widget, 1)
        return panel

    @property
    def busy(self): return self.task is not None

    # ==========================================================
    # NUEVOS MÉTODOS: Lógica del ComboBox
    # ==========================================================
    def _refresh_test_cases(self):
        """Escanea la carpeta y llena el ComboBox con las gramáticas disponibles."""
        self.test_combo.blockSignals(True)
        self.test_combo.clear()
        self.test_combo.addItem("--- Seleccionar prueba ---", None)
        
        if EXAMPLES_DIR.exists():
            # Busca archivos que terminen en .grammar.txt o .sem.txt
            for p in sorted(EXAMPLES_DIR.glob("*.txt")):
                if p.name.endswith(".grammar.txt") or p.name.endswith(".sem.txt"):
                    self.test_combo.addItem(p.name, p)
                    
        self.test_combo.blockSignals(False)

    def _on_test_selected(self, index):
        """Cuando el usuario elige del combo, carga gramática y fuente."""
        if index <= 0: return
        path = self.test_combo.itemData(index)
        if path:
            self._load_test_case(path)

    def _load_test_case(self, grammar_path):
        try:
            text = read_text(grammar_path)
            self.grammar = SemanticGrammarReader.from_text(text)
            self.grammar_text = text
            self.grammar_path = Path(grammar_path)
            
            self.grammar_view.setPlainText("\n".join(_grammar_lines(self.grammar)))
            self.actions_view.setPlainText("\n".join(_action_lines(self.grammar)))
            self.grammar_label.setText(str(self.grammar_path))
            self._build_table()

            # Auto-cargar el código fuente
            candidates = _source_candidates(self.grammar_path)
            if candidates:
                self._set_source(candidates[0])
            else:
                self.source_view.clear()
                self.source_path = None
                self.source_label.setText("No se encontró archivo ProFuente pareja (ej. Prueba1.ProFuente.txt).")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al leer gramática:\n{e}")

    # ==========================================================

    def load_grammar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Gramática Semántica", str(EXAMPLES_DIR),
            "Gramática semántica (*.grammar.txt *.sem.txt);;Texto (*.txt);;Todos (*)"
        )
        if not path: return
        self.test_combo.setCurrentIndex(0) # Quitar selección del combo
        self._load_test_case(Path(path))

    def load_source(self):
        start = str(self.grammar_path.parent if self.grammar_path else EXAMPLES_DIR)
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Código", start, "Texto (*.txt *.pas);;Todos (*)"
        )
        if not path: return
        try:
            self._set_source(Path(path))
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def _set_source(self, path):
        self.source_view.setPlainText(read_text(path))
        self.source_path = path
        self.source_label.setText(str(path))

    def clear_run(self):
        if self.results_window is not None:
            self.results_window.close()
            self.results_window = None
        if self.table:
            self.status.setText("Corrida limpia. Puedes volver a analizar.")

    def clear_all(self):
        if self.busy: return
        self.clear_run()
        self.grammar = None
        self.grammar_text = ""
        self.grammar_path = None
        self.source_path = None
        self.table = self.first = self.follow = self.collection = None
        self.grammar_view.clear()
        self.actions_view.clear()
        self.source_view.clear()
        self.grammar_label.setText("Ninguna gramática seleccionada")
        self.source_label.setText("Ningún código seleccionado (también puedes escribirlo)")
        self.btn_analyze.setEnabled(False)
        self.test_combo.setCurrentIndex(0)
        self.status.setText("Carga una gramática semántica para comenzar.")

    def _build_table(self):
        if not self.grammar: return
        self.status.setText("Construyendo tabla SLR...")
        self.btn_analyze.setEnabled(False)
        self.task = Task(lambda: self._compute_table(self.grammar), self)
        self.task.completed.connect(self._on_table_built)
        self.task.failed.connect(lambda err: QMessageBox.warning(self, "Error de tabla", err))
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
        self.btn_analyze.setEnabled(True)
        name = self.grammar_path.name if self.grammar_path else "gramática"
        conflicts = len(self.table.conflicts)
        note = "" if not conflicts else " (se resuelven desplazando; revisa Conflictos)"
        self.status.setText(f"{name}: tabla lista con {conflicts} conflicto(s){note}.")

    def analyze(self):
        code = self.source_view.toPlainText().strip()
        if not code or not self.table: return

        self.status.setText("Ejecutando análisis semántico...")
        self.btn_analyze.setEnabled(False)
        self.task = Task(lambda: self._run(code), self)
        self.task.completed.connect(self._show_results)
        self.task.failed.connect(lambda err: QMessageBox.warning(self, "Error de análisis", err))
        self.task.finished.connect(self._finish_task)
        self.task.start()

    def _run(self, code):
        lex_res = analyze_code(code, mode="pascal")
        raw_tokens = [t for t in lex_res["tokens"] if t.type.name != "EOF"]
        mapped = tokens_to_terminals(lex_res["tokens"], self.grammar.terminals)
        positions = [(t.line, t.column) for t in raw_tokens]

        parser = SemanticParser(self.table, mapped, positions)
        parse_res = parser.parse()

        state_rows = [["Estado", "Ítem"]]
        for i, state in enumerate(self.collection.states):
            for item in state:
                state_rows.append([f"I{i}", str(item)])

        transition_rows = [["Origen", "Símbolo", "Destino", "Aceptación"]]
        for origin, symbol, target in self.collection.transitions:
            accepting = "Sí" if target in self.collection.acceptation else ""
            transition_rows.append([f"I{origin}", str(symbol), f"I{target}", accepting])

        token_rows = [["Línea", "Lexema", "Token", "Terminal", "Valor léxico"]]
        for token, (lexeme, terminal) in zip(raw_tokens, mapped):
            valex = lexeme if lexeme != terminal else ""
            token_rows.append([token.line, lexeme, token.type.name, terminal, valex])
        token_rows.append(["", "$", "EOF", "$", ""])

        error_rows = [["Tipo", "Línea", "Descripción"]]
        for err in lex_res["errors"]:
            error_rows.append(["Léxico", err["line"], err["description"]])
        for err in parser.semantic_errors:
            error_rows.append(["Semántico", "", err])
        if not parse_res.accepted:
            error_rows.append(["Sintáctico", "", parse_res.error])

        if parse_res.accepted:
            result_rows = [["Resultado (traducción / evaluación)"], [str(parse_res.final_value)]]
        else:
            result_rows = [["Error"], [str(parse_res.error)]]

        results = {
            "Corrida Semántica (Pila)": parse_res.step_rows(),
            "Resultado Evaluado": result_rows,
            "Derivación": parse_res.derivation_rows(),
            "Árbol": parse_res.tree_rows(),
            "Tira de Tokens": token_rows,
            "Tabla de errores": error_rows,
            "Gramática": [["#", "Producción"]] + [
                line.split(". ", 1) for line in _grammar_lines(self.grammar)],
            "Acciones semánticas": [["#", "Acción"]] + [
                line.split(". ", 1) for line in _action_lines(self.grammar)],
            "Programa Fuente": [["Línea", "Código"]] + [[i+1, line] for i, line in enumerate(code.splitlines())],
            "PRIMEROS": _set_rows(self.first),
            "SIGUIENTES": _set_rows(self.follow),
            "Estados": state_rows,
            "Transiciones": transition_rows,
            "Tabla unificada": self.table.combined_rows(),
            "ACTION": self.table.action_rows(),
            "GOTO": self.table.goto_rows(),
        }

        if self.table.conflicts:
            results["Conflictos"] = self.table.conflict_rows()

        return results

    def _show_results(self, results):
        if self.results_window is None or not self.results_window.isVisible():
            self.results_window = ResultsWindow("Salida Semántica", results)
            self.results_window.show()
        else:
            self.results_window.update_results(results)

        self.status.setText("Análisis semántico terminado. Revisa la ventana de resultados.")
        self.btn_analyze.setEnabled(True)

    def _finish_task(self):
        self.task = None
        self.btn_analyze.setEnabled(bool(self.table))