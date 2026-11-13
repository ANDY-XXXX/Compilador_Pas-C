"""Mapeo de tokens del lexer a terminales de la gramática."""

DEFAULT_MAP = {
    "IDENTIFIER": "id",
    "INTEGER_LITERAL": "num",
    "REAL_LITERAL": "realnum", 

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
    "LBRACE": "{",
    "RBRACE": "}",
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

def _as_candidates(mapped):
    if isinstance(mapped, (list, tuple, set)):
        return list(mapped)
    return [mapped]

def _as_names(terminals):
    return [str(t) for t in terminals]

def _string_content(lexeme):
    if len(lexeme) >= 2 and lexeme[0] in ("'", '"') and lexeme[-1] == lexeme[0]:
        return lexeme[1:-1]
    return lexeme

def map_token(token, terminals, custom_map=None):
    name = _type_name(token.type)
    lexeme = token.value

    terminal_names = _as_names(terminals)
    terminal_set = set(terminal_names)

    # --- Caso especial: STRING vs literalCad ---
    if name == "STRING":
        if "literalCad" in terminal_set:
            return "literalCad"

    if custom_map and name in custom_map:
        for candidate in _as_candidates(custom_map[name]):
            if candidate in terminal_set:
                return candidate

    if name in terminal_set:
        return name

    lower_name = name.lower()
    for t in terminal_names:
        if t.lower() == lower_name:
            return t

    if lexeme in terminal_set:
        return lexeme

    if name in DEFAULT_MAP:
        for candidate in _as_candidates(DEFAULT_MAP[name]):
            if candidate in terminal_set:
                return candidate

    return name

def tokens_to_terminals(tokens, grammar_terminals, custom_map=None):
    result = []
    for token in tokens:
        if _type_name(token.type) == "EOF":
            break
        result.append((
            token.value,
            map_token(token, grammar_terminals, custom_map),
        ))
    return result