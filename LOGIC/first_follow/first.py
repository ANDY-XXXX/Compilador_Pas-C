
EPSILON = "ε"

def first(grammar):
    first_sets = {}

    # Terminals: FIRST(t) = {t}
    for terminal in grammar.terminals:
        first_sets[terminal] = {terminal.name}

    # Non-terminals: start empty
    for non_terminal in grammar.not_terminals:
        first_sets[non_terminal] = set()

    # Iterate until nothing changes
    changed = True
    while changed:
        changed = False

        for production in grammar.productions:
            left = production.left
            first_sets.setdefault(left, set())
            size_before = len(first_sets[left])

            # Empty production: add ε
            if not production.right:
                first_sets[left].add(EPSILON)
            else:
                all_derive_epsilon = True

                for symbol in production.right:
                    # Make sure the symbol is registered
                    if symbol not in first_sets:
                        first_sets[symbol] = (
                            {symbol.name} if symbol.is_terminal else set()
                        )

                    # Copy its FIRST set (excluding ε)
                    first_sets[left] |= first_sets[symbol] - {EPSILON}

                    # If this symbol can't derive ε, stop here
                    if EPSILON not in first_sets[symbol]:
                        all_derive_epsilon = False
                        break

                # If every symbol can derive ε, the whole production can too
                if all_derive_epsilon:
                    first_sets[left].add(EPSILON)

            if len(first_sets[left]) != size_before:
                changed = True

    return first_sets


def calculate_first(grammar):
    result = first(grammar)

    return {
        str(non_terminal): result[non_terminal]
        for non_terminal in grammar.not_terminals
    }