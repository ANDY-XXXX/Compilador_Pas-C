class Grammar:
    def __init__(self):
        self.terminals = set()
        self.not_terminals = set()
        self.productions = []
        self.start_symbol = None

    # Construction
    def add_terminal(self, terminal):
        self.terminals.add(terminal)

    def add_not_terminal(self, not_terminal):
        self.not_terminals.add(not_terminal)

    def add_production(self, production):
        self.productions.append(production)

    # Lookup
    def get_production(self, not_terminal):
        return [
            production
            for production in self.productions
            if production.left == not_terminal
        ]


    # Display
    def __str__(self) -> str:
        lines = ["Non-terminals:"]
        for symbol in sorted(self.not_terminals, key=str):
            lines.append(f"  {symbol}")

        lines.append("Terminals:")
        for symbol in sorted(self.terminals, key=str):
            lines.append(f"  {symbol}")

        lines.append("Start symbol:")
        lines.append(f"  {self.start_symbol}")

        lines.append("Productions:")
        for production in self.productions:
            lines.append(f"  {production}")

        return "\n".join(lines)

    def __repr__(self) -> str:
        return (
            f"Grammar(terminals={len(self.terminals)}, "
            f"not_terminals={len(self.not_terminals)}, "
            f"productions={len(self.productions)}, "
            f"start={self.start_symbol})"
        )

    def show(self):
        print(self)