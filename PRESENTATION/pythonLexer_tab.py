from LOGIC.python_lexer.analyzer import analyze_code
from .lexer_base import LexerTabBase


class PythonLexerTab(LexerTabBase):
    def __init__(self, parent=None):
        super().__init__("Analizador léxico · Python", "pythonLexer", parent)

    def analyze(self):
        code = self.editor.toPlainText()
        if not code.strip():
            self.status.setText("Abre o escribe un programa antes de analizar.")
            return

        self.start_task(
            lambda: analyze_code(code),
            self.show_result,
            "Analizando con Python…",
        )

    def show_result(self, result):
        results = {
            "Tokens": [["Línea", "Columna", "Lexema", "Token"]] +
                      [[t.line, t.column, t.value, t.type.name]
                       for t in result["tokens"]],
            "Símbolos": [["Nombre"]] +
                        [[name] for name in result["symbols"]],
            "Errores": [["No. línea", "Descripción"]] +
                       [[e["line"], e["description"]]
                        for e in result["errors"]],
        }

        subtitle = (
            f"{len(result['tokens'])} tokens · "
            f"{len(result['errors'])} errores."
        )
        if result["warning"]:
            subtitle += " · " + result["warning"]

        self.status.setText(subtitle)
        self._show_results("Tokens · Python", results, subtitle)