class Production:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __str__(self) -> str:
        right = " ".join(str(symbol) for symbol in self.right) or "ε"
        return f"{self.left} -> {right}"

    def __repr__(self) -> str:
        return self.__str__()