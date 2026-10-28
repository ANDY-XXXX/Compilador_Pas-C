from .elementLR0 import ElementLR0


class Canonical_Collection:
	# Builds the canonical collection of LR(0) items for a grammar.
    def __init__(self, grammar, end_symbol_name="$"):
        self.grammar = grammar
        self.end_symbol_name = end_symbol_name

        self.states = []          # List of states; each state is a list of ElementLR0
        self.transitions = []     # List of tuples (origin, symbol, target)
        self.acceptation = set()  # Indexes of accepting states (reached by $)

    def closure(self, items):
        result = list(items)
        changed = True

        while changed:
            changed = False
            new_items = []

            for item in result:
                symbol = item.symbol_next_point()

                if symbol is None:
                    continue

                if not symbol.is_terminal:
                    for production in self.grammar.get_production(symbol):
                        new_item = ElementLR0(production.left, production.right, 0)

                        if new_item not in result and new_item not in new_items:
                            new_items.append(new_item)
                            changed = True

            result.extend(new_items)

        return result

    def go_to(self, items, symbol):
        # Goto(I, X): move the dot over X and apply closure.
        moved_items = []

        for item in items:
            next_symbol = item.symbol_next_point()

            if next_symbol is not None and next_symbol == symbol:
                advanced = item.advance_the_point()
                if advanced is not None:
                    moved_items.append(advanced)

        return self.closure(moved_items)

    def canonical_collection(self):
        initial_production = self.grammar.productions[0]
        initial_item = ElementLR0(
            initial_production.left,
            initial_production.right,
            0
        )

        self.states.append(self.closure([initial_item]))

        processed = 0
        while processed < len(self.states):
            index = processed
            state = self.states[index]
            symbols = self._symbols_after_point(state)

            for symbol in symbols:
                new_state = self.go_to(state, symbol)

                if not new_state:
                    continue

                target = self.find_state(new_state)

                if target == -1:
                    self.states.append(new_state)
                    target = len(self.states) - 1

                    if symbol.name == self.end_symbol_name:
                        self.acceptation.add(target)

                transition = (index, symbol, target)
                if transition not in self.transitions:
                    self.transitions.append(transition)

            processed += 1

        return self.states

    # Helpers

    def _symbols_after_point(self, state):
        symbols = set()
        for item in state:
            symbol = item.symbol_next_point()
            if symbol is not None:
                symbols.add(symbol)
        return sorted(symbols, key=lambda s: (not s.is_terminal, str(s)))

    def find_state(self, state):
        for index, existing in enumerate(self.states):
            if self.same_state(existing, state):
                return index
        return -1

    def same_state(self, a, b):
        return set(a) == set(b)

    # Debugging
    def show(self):
        for index, state in enumerate(self.states):
            print(f"I{index} = {{")
            for item in state:
                print(f"    {item}")
            print("}")

        print("\nTransitions:")
        for (origin, symbol, target) in self.transitions:
            print(f"  I{origin} --{symbol}--> I{target}")

        print("\nAccepting states:", self.acceptation)