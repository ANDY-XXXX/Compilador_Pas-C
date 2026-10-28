from dataclasses import dataclass

from .token_type import TokenType


@dataclass
class Variable:
    name: str
    line: int

    def __str__(self) -> str:
        return f"{self.name:<15} Line:{self.line}"


class VariableTableBuilder:
    def __init__(self):
        self.variables = {}

    def build_from_tokens(self, tokens) -> dict:
        self.variables = {}
        inside_var = False
        reading_type = False
        waiting_params = False
        pending = []

        for token in tokens:
            if token.type == TokenType.STRING:
                continue

            word = token.value.lower()

            if word == "var":
                inside_var = True
                reading_type = False
                waiting_params = False
                pending = []
                continue

            # Skip procedure/function declarations: their parameters are
            # handled by the '(' that follows the name.
            if word in {"procedure", "function"}:
                inside_var = False
                reading_type = False
                waiting_params = True
                pending = []
                continue

            if word in {"begin", "end", "const", "type"}:
                inside_var = False
                reading_type = False
                waiting_params = False
                pending = []
                continue

            if waiting_params:
                if token.type == TokenType.LPAREN:
                    inside_var = True
                    waiting_params = False
                    pending = []
                continue

            if not inside_var:
                continue

            if token.type == TokenType.RPAREN:
                # Closes the parameter list; anything after (e.g. the
                # ": integer" return type) is not a variable.
                inside_var = False
                reading_type = False
                pending = []
                continue

            if token.type == TokenType.COLON:
                for name, line in pending:
                    key = name.lower()
                    if key not in self.variables:
                        self.variables[key] = Variable(name=name, line=line)

                pending = []
                reading_type = True

            elif token.type == TokenType.SEMICOLON:
                pending = []
                reading_type = False

            elif (
                token.type == TokenType.IDENTIFIER
                and not reading_type
            ):
                pending.append((token.value, token.line))

        return self.variables