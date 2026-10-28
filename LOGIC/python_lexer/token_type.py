from enum import Enum, auto


class TokenType(Enum):
    # Palabras reservadas
    PROGRAM = auto()
    VAR = auto()
    CONST = auto()
    BEGIN = auto()
    END = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    WHILE = auto()
    DO = auto()
    FOR = auto()
    TO = auto()
    DOWNTO = auto()
    REPEAT = auto()
    UNTIL = auto()
    PROCEDURE = auto()
    FUNCTION = auto()
    ARRAY = auto()
    OF = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    DIV = auto()
    MOD = auto()
    TYPE = auto()
    RECORD = auto()
    CASE = auto()
    RANGE = auto()

    # Tipos de dato
    INTEGER = auto()
    REAL = auto()
    BOOLEAN = auto()
    CHAR = auto()
    STRING_TYPE = auto()
    INTEGER_LITERAL = auto()
    REAL_LITERAL = auto()

    # Literales booleanos
    TRUE = auto()
    FALSE = auto()

    # Identificadores y literales
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # Operadores aritmeticos
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()

    # Operadores relacionales / asignacion
    ASSIGN = auto()         # :=
    EQUAL = auto()          # =
    NOT_EQUAL = auto()      # <>
    LESS = auto()           # <
    LESS_EQUAL = auto()     # <=
    GREATER = auto()        # >
    GREATER_EQUAL = auto()  # >=

    # Simbolos
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()

    COLON = auto()
    SEMICOLON = auto()
    COMMA = auto()
    DOT = auto()

    ARROBA = auto()
    POINTER = auto()
    ASCII = auto()

    EOF = auto()


# Palabras reservadas del lenguaje:
RESERVED_WORDS = {
    "program": TokenType.PROGRAM,
    "var": TokenType.VAR,
    "const": TokenType.CONST,
    "begin": TokenType.BEGIN,
    "end": TokenType.END,
    "if": TokenType.IF,
    "then": TokenType.THEN,
    "else": TokenType.ELSE,
    "while": TokenType.WHILE,
    "do": TokenType.DO,
    "for": TokenType.FOR,
    "to": TokenType.TO,
    "downto": TokenType.DOWNTO,
    "repeat": TokenType.REPEAT,
    "until": TokenType.UNTIL,
    "procedure": TokenType.PROCEDURE,
    "function": TokenType.FUNCTION,
    "integer": TokenType.INTEGER,
    "real": TokenType.REAL,
    "boolean": TokenType.BOOLEAN,
    "char": TokenType.CHAR,
    "string": TokenType.STRING_TYPE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "array": TokenType.ARRAY,
    "of": TokenType.OF,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "div": TokenType.DIV,
    "mod": TokenType.MOD,
    "type": TokenType.TYPE,
    "record": TokenType.RECORD,
    "case": TokenType.CASE,
}

# Operadores de un solo caracter.
SINGLE_CHAR_TOKENS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.MULTIPLY,
    "/": TokenType.DIVIDE,
    "=": TokenType.EQUAL,
    "<": TokenType.LESS,
    ">": TokenType.GREATER,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    ":": TokenType.COLON,
    ";": TokenType.SEMICOLON,
    ",": TokenType.COMMA,
    ".": TokenType.DOT,
    "@": TokenType.ARROBA,
    "^": TokenType.POINTER,
}
