from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QPushButton, QFileDialog, QPlainTextEdit, QTabWidget,
)

from LOGIC.flex_lexer.flex_runner import FlexRunner, DEFAULT_SOURCE
from .lexer_base import LexerTabBase


class FlexLexerTab(LexerTabBase):
    def __init__(self, parent=None):
        super().__init__("Analizador léxico · Flex", "flexLexer", parent)

        self.runner = FlexRunner()

        self.select_button = QPushButton("Seleccionar .l")
        self.compile_button = QPushButton("Compilar Flex")
        self.controls.insertWidget(0, self.select_button)
        self.controls.insertWidget(1, self.compile_button)
        self.buttons += [self.select_button, self.compile_button]

        self.select_button.clicked.connect(self.select_flex)
        self.compile_button.clicked.connect(self.compile)

        self.bottom_tabs = QTabWidget()
        self.bottom_tabs.setMinimumHeight(170)
        self.bottom_tabs.setMaximumHeight(260)

        self.source_view = QPlainTextEdit()
        self.source_view.setReadOnly(True)
        self.source_view.setFont(QFont("Monospace", 10))
        self.source_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setFont(QFont("Monospace", 10))
        self.log.setPlaceholderText(
            "Aquí aparecerá la salida de Flex y GCC al compilar."
        )

        self.bottom_tabs.addTab(self.source_view, "Fuente Flex (.l)")
        self.bottom_tabs.addTab(self.log, "Log de compilación")
        self.layout.insertWidget(self.layout.count() - 1, self.bottom_tabs)

        self._load_flex_source(self.runner.source)

    def _load_flex_source(self, source):
        source = Path(source)
        header = f"// Archivo: {source}\n// {'=' * 62}\n\n"
        if not source.exists():
            self.source_view.setPlainText(header + "[Archivo no encontrado.]")
            return
        try:
            content = source.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            self.source_view.setPlainText(header + f"[Error: {error}]")
            return
        self.source_view.setPlainText(header + content)

    def select_flex(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Flex",
            str(DEFAULT_SOURCE.parent), "Flex (*.l)",
        )
        if not path:
            return
        self.runner = FlexRunner(Path(path))
        self._load_flex_source(self.runner.source)
        self.bottom_tabs.setCurrentWidget(self.source_view)
        self.log.setPlainText(
            f"Fuente Flex seleccionada: {path}\n"
            "Presiona \"Compilar Flex\" para generar el analizador."
        )
        self.status.setText(
            f"Archivo .l cargado: {Path(path).name}. Compílalo antes de analizar."
        )

    def compile(self):
        self.bottom_tabs.setCurrentWidget(self.log)
        self.start_task(
            self.runner.compile, self.compiled,
            "Generando y compilando Flex…",
        )

    def compiled(self, log):
        self.log.setPlainText(log)
        self.bottom_tabs.setCurrentWidget(self.log)
        self.status.setText(
            "Flex compilado. Abre o escribe código Pascal y presiona Analizar."
        )

    def analyze(self):
        code = self.editor.toPlainText()
        if not code.strip():
            self.status.setText("Abre o escribe un programa antes de analizar.")
            return
        self.start_task(
            lambda: self.runner.analyze(code),
            self.show_result,
            "Analizando con Flex…",
        )

    def show_result(self, result):
        results = {
            "Tokens": result.tokens,
            "Símbolos": result.symbols,
            "Errores": result.errors,
        }
        subtitle = (
            f"{len(result.tokens) - 1} tokens · "
            f"{len(result.errors) - 1} errores."
        )
        self.status.setText(subtitle)
        if result.log:
            self.log.setPlainText(result.log)
        self._show_results("Tokens · Flex", results, subtitle)

    def show_error(self, message):
        self.log.setPlainText(message)
        self.bottom_tabs.setCurrentWidget(self.log)
        super().show_error(message)