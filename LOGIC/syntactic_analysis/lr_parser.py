"""Analizador sintáctico LR (SLR(1)) con trazado paso a paso."""

from dataclasses import dataclass, field
from typing import Optional

from .lr_table import ActionType


@dataclass
class ParseNode:
    symbol: str
    children: list = field(default_factory=list)
    is_terminal: bool = False

    def to_text(self, indent=0):
        lines = ["  " * indent + self.symbol]
        for child in self.children:
            lines.append(child.to_text(indent + 1))
        return "\n".join(lines)


@dataclass
class ParseStep:
    step: int
    stack: str
    input: str
    action: str


@dataclass
class ParseResult:
    accepted: bool
    steps: list = field(default_factory=list)
    derivation: list = field(default_factory=list)
    tree: Optional[ParseNode] = None
    error: Optional[str] = None

    def step_rows(self):
        rows = [["Paso", "Pila", "Entrada", "Salida"]]
        for s in self.steps:
            rows.append([s.step, s.stack, s.input, s.action])
        return rows

    def derivation_rows(self):
        rows = [["#", "Producción aplicada"]]
        for i, prod in enumerate(self.derivation, 1):
            rows.append([i, prod])
        return rows

    def tree_rows(self):
        if self.tree is None:
            return [["Árbol sintáctico"], ["(no construido)"]]
        return [["Árbol sintáctico"]] + [
            [line] for line in self.tree.to_text().splitlines()
        ]


def _format_stack(state_stack, symbol_stack):
    parts = []
    for i, state in enumerate(state_stack):
        parts.append(str(state))
        if i < len(symbol_stack):
            parts.append(str(symbol_stack[i]))
    return " ".join(parts)


def _format_input(tokens, index):
    return " ".join(t for _, t in tokens[index:])


class LRParser:
    def __init__(self, table, tokens):
        """
        table:  LRTable ya construida.
        tokens: lista de (lexema, terminal); si no termina en '$', se agrega.
        """
        self.table = table
        self.tokens = list(tokens)
        if not self.tokens or self.tokens[-1][1] != "$":
            self.tokens.append(("$", "$"))

    def parse(self):
        state_stack = [0]
        symbol_stack = []
        node_stack = []
        index = 0
        steps = []
        derivation = []
        step = 0
        max_steps = 10000

        while step < max_steps:
            step += 1
            current_state = state_stack[-1]
            lexeme, terminal = self.tokens[index]
            remaining = _format_input(self.tokens, index)
            action = self.table.action.get((current_state, terminal))

            if action is None:
                steps.append(ParseStep(
                    step,
                    _format_stack(state_stack, symbol_stack),
                    remaining,
                    f"ERROR: sin acción para ({current_state}, '{terminal}')",
                ))
                return ParseResult(
                    accepted=False, steps=steps, derivation=derivation,
                    error=f"No existe acción en el estado I{current_state} "
                          f"para el terminal '{terminal}' (lexema '{lexeme}').",
                )

            if action.type == ActionType.SHIFT:
                steps.append(ParseStep(
                    step,
                    _format_stack(state_stack, symbol_stack),
                    remaining,
                    f"Desplazar a I{action.target} ('{terminal}')",
                ))
                symbol_stack.append(terminal)
                node_stack.append(ParseNode(terminal, is_terminal=True))
                state_stack.append(action.target)
                index += 1

            elif action.type == ActionType.REDUCE:
                production = self.table.grammar.productions[action.production]
                right_len = len(production.right)
                nt = str(production.left)

                steps.append(ParseStep(
                    step,
                    _format_stack(state_stack, symbol_stack),
                    remaining,
                    f"Reducir por {production}",
                ))
                derivation.append(str(production))

                if right_len:
                    children = node_stack[-right_len:]
                    del node_stack[-right_len:]
                    del state_stack[-right_len:]
                    del symbol_stack[-right_len:]
                else:
                    children = []

                node_stack.append(ParseNode(nt, children=children))
                symbol_stack.append(nt)

                top_state = state_stack[-1]
                goto_target = self.table.goto.get((top_state, nt))
                if goto_target is None:
                    return ParseResult(
                        accepted=False, steps=steps, derivation=derivation,
                        error=f"No hay GOTO desde I{top_state} con '{nt}'.",
                    )
                state_stack.append(goto_target)

            elif action.type == ActionType.ACCEPT:
                steps.append(ParseStep(
                    step,
                    _format_stack(state_stack, symbol_stack),
                    remaining,
                    "ACEPTAR",
                ))
                root = None
                if node_stack:
                    if len(node_stack) == 1:
                        root = node_stack[0]
                    else:
                        root = ParseNode("<programa>", children=list(node_stack))
                return ParseResult(
                    accepted=True, steps=steps, derivation=derivation,
                    tree=root,
                )

            else:
                return ParseResult(
                    accepted=False, steps=steps, derivation=derivation,
                    error=f"Acción desconocida: {action}",
                )

        return ParseResult(
            accepted=False, steps=steps, derivation=derivation,
            error="Se excedió el número máximo de pasos.",
        )


def parse_tokens(table, tokens):
    return LRParser(table, tokens).parse()