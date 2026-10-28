from typing import Optional

from .exceptions import LexicalError
from .tokens import Token
from .token_type import (
    RESERVED_WORDS,
    SINGLE_CHAR_TOKENS,
    TokenType,
)


class Lexer:
    # Scans Pascal source text and produces tokens one at a time.

    def __init__(self, text: str):
        self.text = text.replace("\r\n", "\n").replace("\r", "\n")
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

    # ------------------------------------------------------------------
    # Whitespace and comments
    # ------------------------------------------------------------------

    def skip_whitespace(self) -> None:
        """Skips spaces, tabs and newlines."""
        while self.current_char() is not None and self.current_char().isspace():
            self.advance()

    def skip_comment(self) -> None:
        """Skips a block comment, either { ... } or (* ... *)."""
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

    # ------------------------------------------------------------------
    # Lexeme recognition
    # ------------------------------------------------------------------

    def read_identifier(self) -> Token:
        """Reads an identifier or reserved word."""
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
        """Reads an integer or real literal."""
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

    def read_string(self) -> Optional[Token]:
        """Reads a single-quoted string. Returns None if unterminated."""
        start_line, start_col = self.line, self.column
        lexeme = "'"
        self.advance()  # consume the opening quote

        while self.current_char() is not None:
            c = self.current_char()

            # A string cannot span multiple lines.
            if c == "\n":
                break

            if c == "'":
                lexeme += c
                self.advance()

                # Two consecutive quotes represent one literal quote.
                if self.current_char() == "'":
                    lexeme += "'"
                    self.advance()
                    continue

                # A single quote closes the string.
                return Token(
                    TokenType.STRING,
                    lexeme,
                    start_line,
                    start_col,
                )

            lexeme += c
            self.advance()

        # Reached newline or EOF without a closing quote.
        self.errors.append({
            "line": start_line,
            "column": start_col,
            "description": "Error: unclosed string; missing closing quote",
        })

        return None

    def read_double_char_operator(self) -> Optional[Token]:
        """Tries to recognize two-character operators (:=, <=, >=, <>, ..).

        Returns the Token if there is a match, or None otherwise.
        """
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

    # ------------------------------------------------------------------
    # Main API
    # ------------------------------------------------------------------

    def get_next_token(self) -> Token:
        """Returns the next token in the stream, or an EOF token at the end."""
        while self.current_char() is not None:

            # Whitespace
            if self.current_char().isspace():
                self.skip_whitespace()
                continue

            # Single-line comment: // ...
            if self.current_char() == "/" and self.peek() == "/":
                while (
                    self.current_char() is not None
                    and self.current_char() != "\n"
                ):
                    self.advance()
                continue

            # Block comment: { ... } or (* ... *)
            if self.current_char() == "{" or (
                self.current_char() == "(" and self.peek() == "*"
            ):
                self.skip_comment()
                continue

            # Identifiers
            if (
                self.current_char().isascii()
                and self.current_char().isalpha()
            ) or self.current_char() == "_":
                return self.read_identifier()

            # Numbers
            if "0" <= self.current_char() <= "9":
                return self.read_number()

            # Strings
            if self.current_char() == "'":
                token = self.read_string()
                if token is not None:
                    return token
                continue

            # Character literals: #65, #0, ...
            if (
                self.current_char() == "#"
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

            # Two-character operators
            double_char_token = self.read_double_char_operator()
            if double_char_token is not None:
                return double_char_token

            line, col = self.line, self.column
            c = self.current_char()

            # Single-character operators and symbols
            if c in SINGLE_CHAR_TOKENS:
                self.advance()
                return Token(SINGLE_CHAR_TOKENS[c], c, line, col)

            # Unknown character: record and continue
            self.errors.append({
                "line": line,
                "column": col,
                "description": f"Error: '{c}' is not part of the language",
            })
            self.advance()

        return Token(TokenType.EOF, "EOF", self.line, self.column)

    def tokenize(self) -> list:
        """Returns the full list of tokens up to and including EOF."""
        tokens = []

        while True:
            token = self.get_next_token()
            tokens.append(token)
            if token.type == TokenType.EOF:
                break

        return tokens