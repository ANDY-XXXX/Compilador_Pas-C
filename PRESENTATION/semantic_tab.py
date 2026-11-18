from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QPlainTextEdit, QFileDialog, QMessageBox, QSplitter
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

def _set_rows(sets):
    return [["No terminal", "Conjunto"]] + [
        [name, "{ " + "  ".join(sorted(values)) + " }"]
        for name, values in sorted(sets.items())
    ]

class SemanticTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grammar = None
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

        controls = QHBoxLayout()
        self.btn_load_grammar = QPushButton("Cargar Gramática (.sem)")
        self.btn_load_grammar.clicked.connect(self.load_grammar)
        controls.addWidget(self.btn_load_grammar)

        self.btn_load_source = QPushButton("Cargar Código Fuente")
        self.btn_load_source.clicked.connect(self.load_source)
        controls.addWidget(self.btn_load_source)

        self.btn_analyze = QPushButton("Ejecutar Análisis Semántico")
        self.btn_analyze.setEnabled(False)
        self.btn_analyze.clicked.connect(self.analyze)
        controls.addWidget(self.btn_analyze)
        controls.addStretch()
        layout.addLayout(controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.grammar_view = QPlainTextEdit()
        self.grammar_view.setReadOnly(True)
        self.grammar_view.setPlaceholderText("Gramática y acciones semánticas...")
        splitter.addWidget(self.grammar_view)

        self.source_view = QPlainTextEdit()
        self.source_view.setPlaceholderText("Programa fuente (ej. 2+3*4)...")
        splitter.addWidget(self.source_view)

        layout.addWidget(splitter, 1)

        self.status = QLabel("Carga una gramática semántica para comenzar.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    @property
    def busy(self): return self.task is not None

    def load_grammar(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Gramática Semántica", 
            str(Path(__file__).resolve().parents[1] / "EXAMPLES" / "semantic"),
            "Texto (*.txt *.sem);;Todos (*)"
        )
        if not path: return
        try:
            text = read_text(path)
            self.grammar = SemanticGrammarReader.from_text(text)
            self.grammar_view.setPlainText(text)
            self._build_table()
            self.status.setText(f"Gramática cargada: {Path(path).name}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error al leer gramática:\n{e}")

    def load_source(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Código", 
            str(Path(__file__).resolve().parents[1] / "EXAMPLES" / "semantic"),
            "Texto (*.txt *.pas);;Todos (*)"
        )
        if not path: return
        try:
            text = read_text(path)
            self.source_view.setPlainText(text)
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

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
        self.status.setText(f"Tabla lista. {len(self.table.conflicts)} conflictos.")

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
        grammar_text = self.grammar_view.toPlainText()
        
        # 1. Tokenizar
        lex_res = analyze_code(code, mode="pascal")
        mapped = tokens_to_terminals(lex_res["tokens"], self.grammar.terminals)
        
        # 2. Ejecutar Parser Semántico
        parser = SemanticParser(self.table, mapped)
        parse_res = parser.parse()
        
        # 3. Formatear salida
        state_rows = [["Estado", "Ítem"]]
        for i, state in enumerate(self.collection.states):
            for item in state:
                state_rows.append([f"I{i}", str(item)])

        transition_rows = [["Origen", "Símbolo", "Destino", "Aceptación"]]
        for origin, symbol, target in self.collection.transitions:
            accepting = "Sí" if target in self.collection.acceptation else ""
            transition_rows.append([f"I{origin}", str(symbol), f"I{target}", accepting])

        # Asegurar que la UI muestre el $ al final de la tira de tokens
        mapped_ui = list(mapped)
        if not mapped_ui or mapped_ui[-1][1] != "$":
            mapped_ui.append(("$", "$"))

        results = {
            "Gramática y Acciones": [["Línea", "Contenido"]] + [[i+1, line] for i, line in enumerate(grammar_text.splitlines())],
            "Programa Fuente": [["Línea", "Código"]] + [[i+1, line] for i, line in enumerate(code.splitlines())],
            "PRIMEROS": _set_rows(self.first),
            "SIGUIENTES": _set_rows(self.follow),
            "Estados": state_rows,
            "Transiciones": transition_rows,
            "Tabla unificada": self.table.combined_rows(),
            "ACTION": self.table.action_rows(),
            "GOTO": self.table.goto_rows(),
            "Tira de Tokens": [["Lexema", "Terminal"]] + [[lex, term] for lex, term in mapped_ui],
            "Corrida Semántica (Pila)": parse_res.step_rows()
        }
        
        if self.table.conflicts:
            results["Conflictos"] = self.table.conflict_rows()
            
        if parse_res.accepted:
            results["Resultado Evaluado"] = [["Valor Final"], [str(parse_res.final_value)]]
        else:
            results["Resultado Evaluado"] = [["Error"], [str(parse_res.error)]]
            
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