from dataclasses import dataclass
from .token_type import TokenType


@dataclass
class Token:
    # A single lexical token with its type, lexeme, line and column.
    type: TokenType
    value: str
    line: int
    column: int

    def __str__(self) -> str:
        return (
            f"{self.type.name:<15} {self.value:<15} "
            f"Line:{self.line} Col:{self.column}"
        )