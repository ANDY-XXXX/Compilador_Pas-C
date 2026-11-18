from PERSISTENCE.grammar_reader import GrammarReader, GrammarError
from GRAMMAR_MODELS.symbol import Symbol
from GRAMMAR_MODELS.production import Production
from GRAMMAR_MODELS.grammar import Grammar

class SemanticGrammarReader(GrammarReader): 
    # We reading grammar and making the increased
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
                if "{" in line and "}" in line:
                    rule_part, action_part = line.split("{", 1)
                    action = action_part.rsplit("}", 1)[0].strip()
                    line = rule_part.strip()
                rules.append((line_number, line.replace("→", "->"), action))
            else:
                raise GrammarError(f"Línea {line_number}: esperaba encabezado o producción.")

        for key in ("No_Terminales", "Terminales", "Inicial"):
            if key not in headers:
                raise GrammarError(f"Falta el encabezado: {key}:")

        non_terminals = headers["No_Terminales"].split()
        terminals = headers["Terminales"].split()
        initial = headers["Inicial"]

        # Asegurar que $ esté en los terminales
        if "$" not in terminals:
            terminals.append("$")

        symbols = {name: Symbol(name, False) for name in non_terminals}
        symbols.update({name: Symbol(name, True) for name in terminals})

        for name in non_terminals: grammar.add_not_terminal(symbols[name])
        for name in terminals: grammar.add_terminal(symbols[name])
        grammar.start_symbol = symbols[initial]

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