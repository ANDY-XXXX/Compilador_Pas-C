import sys

from .exceptions import LexicalError
from .lexer import Lexer
from .symbol_table import VariableTableBuilder
from .token_type import TokenType


def analyze_code(source_code: str) -> dict:
    lexer = Lexer(source_code)
    tokens = []
    warning = None

    try:
        while True:
            token = lexer.get_next_token()
            tokens.append(token)

            if token.type == TokenType.EOF:
                break
    except LexicalError as error:
        warning = str(error)
        lexer.errors.append({
            "line": lexer.line,
            "column": lexer.column,
            "description": str(error),
        })

    builder = VariableTableBuilder()
    variables = builder.build_from_tokens(tokens)

    return {
        "tokens": tokens,
        "errors": lexer.errors,
        "symbols": [variable.name for variable in variables.values()],
        "warning": warning,
    }


def analyze_file(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return analyze_code(file.read())


def main():
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = input("Pascal file (.pas): ")

    result = analyze_file(file_path)

    print("\nTOKENS FOUND\n")
    for token in result["tokens"]:
        print(token)

    print("\nLEXICAL ERRORS\n")
    for error in result["errors"]:
        print(error["line"], error["description"])

    print("\nVARIABLES\n")
    for name in result["symbols"]:
        print(name)

    if result["warning"]:
        print("\nWARNING:", result["warning"])


if __name__ == "__main__":
    main()