"""Mapeo de tokens del lexer a terminales de la gramática."""

DEFAULT_MAP = {
    "IDENTIFIER": "id",
    "INTEGER_LITERAL": "num",
    "REAL_LITERAL": "num",
    "STRING": "str",

    "PROGRAM": "program",
    "VAR": "var",
    "CONST": "const",
    "BEGIN": "begin",
    "END": "end",
    "IF": "if",
    "THEN": "then",
    "ELSE": "else",
    "WHILE": "while",
    "DO": "do",
    "FOR": "for",
    "TO": "to",
    "DOWNTO": "downto",
    "REPEAT": "repeat",
    "UNTIL": "until",
    "PROCEDURE": "procedure",
    "FUNCTION": "function",
    "INTEGER": "integer",
    "REAL": "real",
    "BOOLEAN": "boolean",
    "CHAR": "char",
    "STRING_TYPE": "string",
    "TRUE": "true",
    "FALSE": "false",
    "ARRAY": "array",
    "OF": "of",
    "AND": "and",
    "OR": "or",
    "NOT": "not",
    "DIV": "div",
    "MOD": "mod",
    "TYPE": "type",
    "RECORD": "record",
    "CASE": "case",

    "PLUS": "+",
    "MINUS": "-",
    "MULTIPLY": "*",
    "DIVIDE": "/",
    "ASSIGN": ":=",
    "EQUAL": "=",
    "NOT_EQUAL": "<>",
    "LESS": "<",
    "LESS_EQUAL": "<=",
    "GREATER": ">",
    "GREATER_EQUAL": ">=",

    "LPAREN": "(",
    "RPAREN": ")",
    "LBRACKET": "[",
    "RBRACKET": "]",
    "COLON": ":",
    "SEMICOLON": ";",
    "COMMA": ",",
    "DOT": ".",
    "RANGE": "..",
    "ARROBA": "@",
    "POINTER": "^",
    "ASCII": "ascii",
    "EOF": "$",
}


def _type_name(token_type):
    if hasattr(token_type, "name"):
        return token_type.name
    return str(token_type)


def map_token(token, terminals, custom_map=None):
    name = _type_name(token.type)
    lexeme = token.value
    terminals = list(terminals)

    if custom_map and name in custom_map:
        return custom_map[name]

    # Nombre exacto
    if name in terminals:
        return name

    # Nombre en minúsculas
    for t in terminals:
        if t.lower() == name.lower():
            return t

    # Lexema exacto
    if lexeme in terminals:
        return lexeme

    # Mapa por defecto, solo si el resultado está en la gramática
    if name in DEFAULT_MAP:
        mapped = DEFAULT_MAP[name]
        if mapped in terminals:
            return mapped

    return name


def tokens_to_terminals(tokens, grammar_terminals, custom_map=None):
    """
    Convierte la lista de tokens del lexer a pares (lexema, terminal).
    Omite EOF; el parser agrega su propio '$'.
    """
    result = []
    for token in tokens:
        if _type_name(token.type) == "EOF":
            break
        result.append((
            token.value,
            map_token(token, grammar_terminals, custom_map),
        ))
    return result