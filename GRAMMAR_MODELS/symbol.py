class Symbol:
    def __init__(self, name: str, is_terminal: bool = False):
        self.name = name
        self.is_terminal = is_terminal

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, other) -> bool:
        if not isinstance(other, Symbol):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)