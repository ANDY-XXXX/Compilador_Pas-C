from typing import Optional

from .exceptions import LexicalError
from .tokens import Token
from .token_type import (
    RESERVED_WORDS,
    SINGLE_CHAR_TOKENS,
    TokenType,
)


class Lexer:
    # Scans source text and produces tokens one at a time.

    def __init__(self, text: str, mode: str = "pascal"):
        self.text = text.replace("\r\n", "\n").replace("\r", "\n")
        self.mode = mode
        self.position = 0
        self.line = 1
        self.column = 1
        self.errors = []

    # Basic reading helpers
    def current_char(self) -> Optional[str]:
        if self.position >= len(self.text):
            return None
        return self.text[self.position]

    def peek(self) -> Optional[str]:
        next_pos = self.position + 1
        if next_pos >= len(self.text):
            return None
        return self.text[next_pos]

    def advance(self) -> None:
        char = self.current_char()

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        self.position += 1

    # Whitespace and comments

    def skip_whitespace(self) -> None:
        while self.current_char() is not None and self.current_char().isspace():
            self.advance()

    def skip_block_comment_pascal(self) -> None:
        start_line = self.line
        start_col = self.column

        if self.current_char() == "{":
            closing = "}"
            self.advance()
        elif self.current_char() == "(" and self.peek() == "*":
            closing = "*)"
            self.advance()
            self.advance()
        else:
            return

        while self.current_char() is not None:
            if closing == "}" and self.current_char() == "}":
                self.advance()
                return
            if (
                closing == "*)"
                and self.current_char() == "*"
                and self.peek() == ")"
            ):
                self.advance()
                self.advance()
                return
            self.advance()

        self.errors.append({
            "line": start_line,
            "column": start_col,
            "description": f"Error: unclosed comment; missing {closing}",
        })

    def skip_block_comment_c(self) -> None:
        start_line = self.line
        start_col = self.column
        self.advance()  # /
        self.advance()  # *

        while self.current_char() is not None:
            if self.current_char() == "*" and self.peek() == "/":
                self.advance()
                self.advance()
                return
            self.advance()

        self.errors.append({
            "line": start_line,
            "column": start_col,
            "description": "Error: unclosed comment; missing */",
        })

    # Lexeme recognition

    def read_identifier(self) -> Token:
        start_col = self.column
        lexeme = ""

        while self.current_char() is not None and (
            (
                self.current_char().isascii()
                and self.current_char().isalnum()
            )
            or self.current_char() == "_"
        ):
            lexeme += self.current_char()
            self.advance()

        token_type = RESERVED_WORDS.get(lexeme.lower(), TokenType.IDENTIFIER)
        return Token(token_type, lexeme, self.line, start_col)

    def read_number(self) -> Token:
        start_col = self.column
        lexeme = ""
        has_decimal_point = False

        while self.current_char() is not None:
            c = self.current_char()

            if "0" <= c <= "9":
                lexeme += c
                self.advance()
            elif (
                c == "."
                and not has_decimal_point
                and self.peek() is not None
                and "0" <= self.peek() <= "9"
            ):
                has_decimal_point = True
                lexeme += c
                self.advance()
            else:
                break

        token_type = (
            TokenType.REAL_LITERAL
            if has_decimal_point
            else TokenType.INTEGER_LITERAL
        )
        return Token(token_type, lexeme, self.line, start_col)

    def read_string(self, quote: str = "'") -> Optional[Token]:
        """Lee una cadena. El cierre debe ser el mismo `quote`."""
        start_line, start_col = self.line, self.column
        lexeme = quote
        self.advance()

        while self.current_char() is not None:
            c = self.current_char()

            if c == "\n":
                break

            if c == quote:
                lexeme += c
                self.advance()

                # En Pascal '' escapa una comilla; en C \" escapa.
                if self.current_char() == quote:
                    lexeme += quote
                    self.advance()
                    continue

                return Token(
                    TokenType.STRING, lexeme, start_line, start_col,
                )

            lexeme += c
            self.advance()

        self.errors.append({
            "line": start_line,
            "column": start_col,
            "description": "Error: unclosed string; missing closing quote",
        })
        return None

    def read_double_char_operator(self) -> Optional[Token]:
        c = self.current_char()
        line, col = self.line, self.column

        double_char_ops = {
            (":", "="): TokenType.ASSIGN,
            ("<", "="): TokenType.LESS_EQUAL,
            (">", "="): TokenType.GREATER_EQUAL,
            ("<", ">"): TokenType.NOT_EQUAL,
            (".", "."): TokenType.RANGE,
        }

        pair = (c, self.peek())
        if pair in double_char_ops:
            self.advance()
            self.advance()
            return Token(double_char_ops[pair], "".join(pair), line, col)

        return None

    # Main API

    def get_next_token(self) -> Token:
        while self.current_char() is not None:

            if self.current_char().isspace():
                self.skip_whitespace()
                continue

            # Comentario de línea // ... (válido en ambos modos)
            if self.current_char() == "/" and self.peek() == "/":
                while (
                    self.current_char() is not None
                    and self.current_char() != "\n"
                ):
                    self.advance()
                continue

            # Comentarios de bloque según el modo
            if self.mode == "pascal":
                if self.current_char() == "{" or (
                    self.current_char() == "(" and self.peek() == "*"
                ):
                    self.skip_block_comment_pascal()
                    continue
            else:  # mode == "c"
                if self.current_char() == "/" and self.peek() == "*":
                    self.skip_block_comment_c()
                    continue

            # Identificadores
            if (
                self.current_char().isascii()
                and self.current_char().isalpha()
            ) or self.current_char() == "_":
                return self.read_identifier()

            # Números
            if "0" <= self.current_char() <= "9":
                return self.read_number()

            # Cadenas: acepta '...' y "..." en ambos modos
            if self.current_char() in ("'", '"'):
                quote = self.current_char()
                token = self.read_string(quote)
                if token is not None:
                    return token
                continue

            # Literal de caracter Pascal #65
            if (
                self.mode == "pascal"
                and self.current_char() == "#"
                and self.peek() is not None
                and "0" <= self.peek() <= "9"
            ):
                line, col = self.line, self.column
                lexeme = "#"
                self.advance()

                while (
                    self.current_char() is not None
                    and "0" <= self.current_char() <= "9"
                ):
                    lexeme += self.current_char()
                    self.advance()

                return Token(TokenType.ASCII, lexeme, line, col)

            double_char_token = self.read_double_char_operator()
            if double_char_token is not None:
                return double_char_token

            line, col = self.line, self.column
            c = self.current_char()

            if c in SINGLE_CHAR_TOKENS:
                self.advance()
                return Token(SINGLE_CHAR_TOKENS[c], c, line, col)

            self.errors.append({
                "line": line,
                "column": col,
                "description": f"Error: '{c}' is not part of the language",
            })
            self.advance()

        return Token(TokenType.EOF, "EOF", self.line, self.column)

    def tokenize(self) -> list:
        tokens = []
        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break
        return tokens