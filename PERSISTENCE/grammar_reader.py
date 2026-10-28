from GRAMMAR_MODELS.symbol import Symbol
from GRAMMAR_MODELS.production import Production
from GRAMMAR_MODELS.grammar import Grammar
from .text_files import read_text


class GrammarError(ValueError):
    # Raised when the grammar file is incomplete or malformed.
    pass


class GrammarReader:
    # Reads a grammar from a text file and returns a Grammar object.

    def __init__(self, file_path):
        self.file_path = file_path

    def read(self):
        return self.from_text(read_text(self.file_path))

    @staticmethod
    def from_text(text):
        grammar = Grammar()
        headers = {}
        rules = []

        for line_number, raw_line in enumerate(text.splitlines(), 1):
            line = raw_line.strip()
            if not line:
                continue

            key, sep, value = line.partition(":")
            if sep and key in ("No_Terminales", "Terminales", "Inicial"):
                if key in headers:
                    raise GrammarError(
                        f"Line {line_number}: duplicated header: {key}."
                    )
                headers[key] = value.strip()

            elif "->" in line or "→" in line:
                rules.append((line_number, line.replace("→", "->")))

            else:
                raise GrammarError(
                    f"Line {line_number}: expected a header or a production."
                )

        for key in ("No_Terminales", "Terminales", "Inicial"):
            if key not in headers:
                raise GrammarError(f"Missing header: {key}:")

        non_terminals = headers["No_Terminales"].split()
        terminals = headers["Terminales"].split()
        initial = headers["Inicial"]

        if not non_terminals or initial not in non_terminals:
            raise GrammarError("Initial symbol must be a declared non-terminal.")

        if len(set(non_terminals)) != len(non_terminals) or \
           len(set(terminals)) != len(terminals):
            raise GrammarError("Duplicated symbols in declarations.")

        if set(non_terminals) & set(terminals):
            raise GrammarError(
                "A symbol cannot be both a terminal and a non-terminal."
            )

        # ε, |, and the arrows are markers of the format and cannot be
        # declared as symbols. '$' is allowed: it is a valid terminal.
        reserved = {"ε", "|", "->", "→"}
        if reserved & (set(non_terminals) | set(terminals)):
            raise GrammarError(
                "ε, | and the arrows are reserved markers of the format. "
                "They must not be declared as symbols. "
                "'$' is allowed as a terminal."
            )

        symbols = {name: Symbol(name, False) for name in non_terminals}
        symbols.update({name: Symbol(name, True) for name in terminals})

        for name in non_terminals:
            grammar.add_not_terminal(symbols[name])
        for name in terminals:
            grammar.add_terminal(symbols[name])

        grammar.start_symbol = symbols[initial]

        if not rules:
            raise GrammarError("The grammar contains no productions.")

        for line_number, line in rules:
            left, right = (part.strip() for part in line.split("->", 1))

            if left not in non_terminals:
                raise GrammarError(
                    f"Line {line_number}: '{left}' is not a declared non-terminal."
                )

            for alternative in right.split("|"):
                names = alternative.split()
                if names == ["ε"]:
                    names = []

                unknown = [name for name in names if name not in symbols]
                if unknown:
                    raise GrammarError(
                        f"Line {line_number}: undeclared symbols: {unknown}. "
                        "Separate symbols with spaces; ε must appear alone."
                    )

                grammar.add_production(
                    Production(
                        symbols[left],
                        [symbols[name] for name in names],
                    )
                )

        return grammar