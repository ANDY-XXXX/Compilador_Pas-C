import re

from PERSISTENCE.grammar_reader import GrammarReader, GrammarError
from GRAMMAR_MODELS.symbol import Symbol
from GRAMMAR_MODELS.production import Production
from GRAMMAR_MODELS.grammar import Grammar

# Acción semántica al final de la regla: "{ ... = ... }".
# Se exige un '=' (o ':=') dentro de las llaves para no confundir la acción
# con terminales '{' '}' de una gramática tipo C.
ACTION_PATTERN = re.compile(r"^(.*?)\s*\{([^{}]*=[^{}]*)\}\s*$")


class SemanticGrammarReader(GrammarReader):
    # Lee la gramática con sus acciones y la aumenta (S' -> S $) si hace falta.
    @staticmethod
    def from_text(text):
        grammar = Grammar()
        headers = {}
        rules = []
        actions = {}

        for line_number, raw_line in enumerate(text.splitlines(), 1):
            line = raw_line.strip()
            if not line: continue

            key, sep, value = line.partition(":")
            if sep and key in ("No_Terminales", "Terminales", "Inicial"):
                headers[key] = value.strip()
            elif "->" in line or "→" in line:
                action = None
                match = ACTION_PATTERN.match(line)
                if match:
                    line = match.group(1).strip()
                    action = match.group(2).strip()
                rules.append((line_number, line.replace("→", "->"), action))
            else:
                raise GrammarError(f"Línea {line_number}: esperaba encabezado o producción.")

        for key in ("No_Terminales", "Terminales", "Inicial"):
            if key not in headers:
                raise GrammarError(f"Falta el encabezado: {key}:")

        non_terminals = headers["No_Terminales"].split()
        terminals = headers["Terminales"].split()
        initial = headers["Inicial"]

        if initial not in non_terminals:
            raise GrammarError(f"El símbolo inicial '{initial}' no está en No_Terminales.")

        # Asegurar que $ esté en los terminales
        if "$" not in terminals:
            terminals.append("$")

        symbols = {name: Symbol(name, False) for name in non_terminals}
        symbols.update({name: Symbol(name, True) for name in terminals})

        for name in non_terminals: grammar.add_not_terminal(symbols[name])
        for name in terminals: grammar.add_terminal(symbols[name])
        grammar.start_symbol = symbols[initial]

        # ¿La gramática ya trae su producción aumentada (Inicial -> X $)?
        # Si es así se usa esa como producción 0 y no se agrega otra.
        already_augmented = None
        for index, (_, line, _) in enumerate(rules):
            left, right = (part.strip() for part in line.split("->", 1))
            names = right.split()
            if left == initial and len(names) == 2 and names[-1] == "$":
                already_augmented = index
                break

        if already_augmented is not None:
            rules.insert(0, rules.pop(already_augmented))
        else:
            # --- INYECCIÓN DE LA PRODUCCIÓN AUMENTADA (Índice 0) ---
            aug_name = initial + "'"
            while aug_name in symbols:
                aug_name += "'"

            aug_symbol = Symbol(aug_name, False)
            grammar.add_not_terminal(aug_symbol)

            aug_prod = Production(aug_symbol, [symbols[initial], symbols["$"]])
            grammar.add_production(aug_prod)

        # --- LECTURA DE REGLAS DEL USUARIO ---
        for line_number, line, action in rules:
            left, right = (part.strip() for part in line.split("->", 1))

            if left not in symbols:
                raise GrammarError(f"Línea {line_number}: '{left}' no está declarado.")

            for alternative in right.split("|"):
                names = alternative.split()
                if names == ["ε"] or names == ["epsilon"]: names = []

                unknown = [name for name in names if name not in symbols]
                if unknown:
                    raise GrammarError(f"Línea {line_number}: símbolos desconocidos: {unknown}.")

                prod = Production(symbols[left], [symbols[name] for name in names])
                grammar.add_production(prod)

                if action:
                    # Guardamos la acción (ej. índice 1, 2, etc.)
                    actions[len(grammar.productions) - 1] = action

        grammar.actions = actions
        return grammar