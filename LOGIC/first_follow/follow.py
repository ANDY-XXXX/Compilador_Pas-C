EPSILON = "ε"
END_SYMBOL = "$"


class FollowError(Exception):
    # Raised when the data needed to compute FOLLOW is invalid.
    pass


class Follow:
    def __init__(self, non_terminals, terminals, start_symbol,
                productions, first_sets):
        self.non_terminals = list(non_terminals)
        self.terminals = list(terminals)
        self.start_symbol = start_symbol
        self.productions = productions          # dict: str -> list[list[str]]
        self.first_sets = first_sets            # dict: str -> set[str]
        self.follow_sets = {nt: set() for nt in self.non_terminals}
        self._validate()

    @classmethod
    def from_grammar(cls, grammar, first_sets):
        initial = str(grammar.start_symbol)
        rest = sorted(
            str(nt) for nt in grammar.not_terminals if str(nt) != initial
        )
        non_terminals = (
            [initial]
            if initial in {str(nt) for nt in grammar.not_terminals}
            else []
        ) + rest
        terminals = sorted(str(t) for t in grammar.terminals)

        productions = {}
        for production in grammar.productions:
            right = [str(symbol) for symbol in production.right] or [EPSILON]
            productions.setdefault(str(production.left), []).append(right)

        first_sets = {
            str(key): {str(value) for value in values}
            for key, values in first_sets.items()
        }

        return cls(non_terminals, terminals, initial, productions, first_sets)

    # Validation
    def _validate(self):
        if self.start_symbol not in self.non_terminals:
            raise FollowError(
                f"Start symbol '{self.start_symbol}' is not a non-terminal."
            )

        known = set(self.non_terminals) | set(self.terminals) | {EPSILON}

        for non_terminal, rules in self.productions.items():
            if non_terminal not in self.non_terminals:
                raise FollowError(
                    f"'{non_terminal}' has productions but is not a non-terminal."
                )
            for rule in rules:
                for symbol in rule:
                    if symbol not in known:
                        raise FollowError(
                            f"Unknown symbol '{symbol}' in a production of "
                            f"'{non_terminal}'."
                        )

        for non_terminal in self.non_terminals:
            if non_terminal not in self.first_sets:
                raise FollowError(
                    f"Missing FIRST set for '{non_terminal}'."
                )

    # Core algorithms

    def _first_of_sequence(self, sequence):
        result = set()

        for symbol in sequence:
            if symbol == EPSILON:
                continue
            if symbol in self.terminals:
                result.add(symbol)
                return result

            first_symbol = self.first_sets[symbol]
            result |= first_symbol - {EPSILON}

            if EPSILON not in first_symbol:
                return result

        result.add(EPSILON)
        return result

    def compute(self):
        # Rule 1: $ belongs to FOLLOW of the start symbol
        self.follow_sets[self.start_symbol].add(END_SYMBOL)

        changed = True
        while changed:
            changed = False

            for non_terminal, rules in self.productions.items():
                for rule in rules:
                    for i, symbol in enumerate(rule):
                        if symbol not in self.follow_sets:
                            continue

                        beta = rule[i + 1:]
                        first_beta = self._first_of_sequence(beta)

                        # Rule 2: FIRST(beta) without ε
                        new_elements = first_beta - {EPSILON}

                        # Rule 3: if beta can derive ε, add FOLLOW(A)
                        if EPSILON in first_beta:
                            new_elements |= self.follow_sets[non_terminal]

                        if not new_elements <= self.follow_sets[symbol]:
                            self.follow_sets[symbol] |= new_elements
                            changed = True

        return self.follow_sets
    
    # Display
    def _sort(self, elements):
        # Sorts a set: $ first, then terminals in declaration order.
        order = [END_SYMBOL] + self.terminals
        return sorted(
            elements,
            key=lambda s: order.index(s) if s in order else len(order),
        )

    def format_sets(self):
        lines = ["FOLLOW"]
        for non_terminal in self.non_terminals:
            elements = " ".join(self._sort(self.follow_sets[non_terminal]))
            lines.append(f"S({non_terminal})={{ {elements} }}")
        return "\n".join(lines)