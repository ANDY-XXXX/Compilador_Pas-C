from .follow import Follow


def calculate_sets(grammar, first_provider):
    first = {
        str(key): {str(value) for value in values}
        for key, values in first_provider(grammar).items()
    }

    expected = {str(nt) for nt in grammar.not_terminals}
    if set(first) != expected:
        raise ValueError(
            "FIRST must contain exactly the non-terminals of the grammar."
        )

    allowed = {str(t) for t in grammar.terminals} | {"ε"}
    if any(values - allowed for values in first.values()):
        raise ValueError("FIRST can only contain terminals and ε.")

    follow = Follow.from_grammar(grammar, first).compute()

    return first, follow