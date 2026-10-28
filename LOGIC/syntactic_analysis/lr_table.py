"""Construcción de la tabla de análisis sintáctico SLR(1)."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class ActionType(Enum):
    SHIFT = auto()
    REDUCE = auto()
    ACCEPT = auto()


@dataclass(frozen=True)
class Action:
    """Una acción de la tabla."""
    type: ActionType
    target: Optional[int] = None        # estado destino, solo para SHIFT
    production: Optional[int] = None    # índice (0-based), solo REDUCE

    def __str__(self) -> str:
        if self.type == ActionType.SHIFT:
            return f"d{self.target}"
        if self.type == ActionType.REDUCE:
            return f"r{self.production + 1}"
        return "acc"


@dataclass(frozen=True)
class Conflict:
    state: int
    terminal: str
    existing: Action
    new: Action

    def __str__(self) -> str:
        return (
            f"Conflicto en I{self.state} con '{self.terminal}': "
            f"{self.existing} vs {self.new}"
        )


class LRTable:
    def __init__(self, grammar, collection, follow_sets):
        self.grammar = grammar
        self.collection = collection
        self.follow_sets = follow_sets

        self._goto_index = {
            (origin, str(symbol)): target
            for origin, symbol, target in collection.transitions
        }

        self.action = {}
        self.goto = {}
        self.conflicts = []

    # ---------------- construcción ----------------

    def build(self):
        augmented_left = str(self.grammar.productions[0].left)

        for i, state in enumerate(self.collection.states):
            for item in state:
                next_symbol = item.symbol_next_point()

                # -------- Shift / Accept --------
                if next_symbol is not None and next_symbol.is_terminal:
                    target = self._goto_index.get((i, str(next_symbol)))
                    if target is None:
                        continue

                    if target in self.collection.acceptation:
                        self._add_action(
                            i, str(next_symbol), Action(ActionType.ACCEPT)
                        )
                    else:
                        self._add_action(
                            i, str(next_symbol),
                            Action(ActionType.SHIFT, target=target),
                        )

                # -------- Reduce --------
                elif item.point_at_the_end():
                    if str(item.left) == augmented_left:
                        continue

                    prod_index = self._production_index(item)
                    nt = str(item.left)

                    for terminal in self.follow_sets.get(nt, set()):
                        self._add_action(
                            i, terminal,
                            Action(ActionType.REDUCE, production=prod_index),
                        )

                # -------- Goto --------
                if next_symbol is not None and not next_symbol.is_terminal:
                    target = self._goto_index.get((i, str(next_symbol)))
                    if target is not None:
                        self.goto[(i, str(next_symbol))] = target

        return self

    # ---------------- helpers ----------------

    def _add_action(self, state, terminal, action):
        key = (state, terminal)
        if key not in self.action:
            self.action[key] = action
            return

        existing = self.action[key]
        if existing == action:
            return

        self.conflicts.append(Conflict(state, terminal, existing, action))

        if action.type == ActionType.ACCEPT:
            self.action[key] = action
        elif existing.type == ActionType.ACCEPT:
            pass
        elif (action.type == ActionType.SHIFT and
              existing.type == ActionType.REDUCE):
            self.action[key] = action

    def _production_index(self, item) -> int:
        for index, production in enumerate(self.grammar.productions):
            if production.left != item.left:
                continue
            if len(production.right) != len(item.right):
                continue
            if all(a == b for a, b in zip(production.right, item.right)):
                return index
        raise LookupError(f"Producción no encontrada: {item}")

    # ---------------- vistas ----------------

    def _terminals(self):
        return sorted(str(t) for t in self.grammar.terminals)

    def _non_terminals(self):
        return sorted(str(nt) for nt in self.grammar.not_terminals)

    def conflict_actions(self, state, terminal):
        actions = []
        for c in self.conflicts:
            if c.state == state and c.terminal == terminal:
                if c.existing not in actions:
                    actions.append(c.existing)
                if c.new not in actions:
                    actions.append(c.new)
        return actions or None

    def format_action(self, state, terminal) -> str:
        conflicted = self.conflict_actions(state, terminal)
        if conflicted:
            return " / ".join(str(a) for a in conflicted)
        action = self.action.get((state, terminal))
        return str(action) if action is not None else ""

    def action_rows(self):
        terminals = self._terminals()
        rows = [["Estado"] + terminals]
        for i in range(len(self.collection.states)):
            rows.append([f"I{i}"] + [
                self.format_action(i, t) for t in terminals
            ])
        return rows

    def goto_rows(self):
        non_terminals = self._non_terminals()
        rows = [["Estado"] + non_terminals]
        for i in range(len(self.collection.states)):
            row = [f"I{i}"]
            for nt in non_terminals:
                target = self.goto.get((i, nt))
                row.append(f"I{target}" if target is not None else "")
            rows.append(row)
        return rows

    def combined_rows(self):
        terminals = self._terminals()
        non_terminals = self._non_terminals()
        rows = [["Estado"] + terminals + non_terminals]
        for i in range(len(self.collection.states)):
            row = [f"I{i}"]
            for t in terminals:
                row.append(self.format_action(i, t))
            for nt in non_terminals:
                target = self.goto.get((i, nt))
                row.append(f"I{target}" if target is not None else "")
            rows.append(row)
        return rows

    def conflict_rows(self):
        if not self.conflicts:
            return [["Estado", "Terminal", "Existente", "Nuevo"]]
        return [["Estado", "Terminal", "Existente", "Nuevo"]] + [
            [f"I{c.state}", c.terminal, str(c.existing), str(c.new)]
            for c in self.conflicts
        ]


# ---------------- atajos ----------------

def build_lr_table(grammar, collection, follow_sets):
    return LRTable(grammar, collection, follow_sets).build()


def build_from_file(path):
    from PERSISTENCE.grammar_reader import GrammarReader
    from LOGIC.canonical_collection import Canonical_Collection
    from LOGIC.first_follow import calculate_sets, calculate_first

    grammar = GrammarReader(path).read()
    collection = Canonical_Collection(grammar)
    collection.canonical_collection()
    _, follow = calculate_sets(grammar, calculate_first)
    return LRTable(grammar, collection, follow).build()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python -m LOGIC.syntactic_analysis.lr_table <gramatica.txt>")
        sys.exit(1)

    table = build_from_file(sys.argv[1])

    print("\n=== ACCIÓN (SLR) ===")
    for row in table.action_rows():
        print("\t".join(row))

    print("\n=== GOTO ===")
    for row in table.goto_rows():
        print("\t".join(row))

    if table.conflicts:
        print(f"\n=== CONFLICTOS ({len(table.conflicts)}) ===")
        for conflict in table.conflicts:
            print(conflict)
    else:
        print("\nSin conflictos: la gramática es SLR(1).")