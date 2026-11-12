DEFAULT_MAP = {
    "IDENTIFIER": "id",
    "INTEGER_LITERAL": "num",
    "REAL_LITERAL": "num",

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
    """Convierte Symbol o str a una lista de nombres (strings)."""
    return [str(t) for t in terminals]


def _string_content(lexeme):
    """Devuelve el contenido de una cadena sin las comillas externas."""
    if len(lexeme) >= 2 and lexeme[0] in ("'", '"') and lexeme[-1] == lexeme[0]:
        return lexeme[1:-1]
    return lexeme


def map_token(token, terminals, custom_map=None):
    name = _type_name(token.type)
    lexeme = token.value

    terminal_names = _as_names(terminals)
    terminal_set = set(terminal_names)

    # --- Caso especial: STRING vs literalCad / literalCar ---
    if name == "STRING":
        content = _string_content(lexeme)
        if len(content) == 1 and "literalCar" in terminal_set:
            return "literalCar"
        if "literalCad" in terminal_set:
            return "literalCad"
        # Si la gramática usa otros nombres, cae a los mapas generales abajo.

    # 1) custom_map explícito
    if custom_map and name in custom_map:
        for candidate in _as_candidates(custom_map[name]):
            if candidate in terminal_set:
                return candidate

    # 2) Nombre exacto
    if name in terminal_set:
        return name

    # 3) Nombre en minúsculas
    lower_name = name.lower()
    for t in terminal_names:
        if t.lower() == lower_name:
            return t

    # 4) Lexema exacto (writeln, readln, break, continue, float, main…)
    if lexeme in terminal_set:
        return lexeme

    # 5) Mapa por defecto
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