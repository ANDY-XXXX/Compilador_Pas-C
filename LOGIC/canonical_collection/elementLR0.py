class ElementLR0:
    def __init__(self, left, right, point=0):
        self.left = left        # Non-terminal on the left side
        self.right = right      # List of Symbols on the right side
        self.point = point      # Position of the dot

    # Return the symbol right after the dot, or None if the dot is at the end
    def symbol_next_point(self):
        if self.point < len(self.right):
            return self.right[self.point]
        return None

    # True if the dot is at the end of the right side
    def point_at_the_end(self):
        return self.point == len(self.right)

    # Return a new item with the dot moved one position to the right
    def advance_the_point(self):
        if self.point_at_the_end():
            return None
        return ElementLR0(self.left, self.right, self.point + 1)

    # Two items are equal if they have the same production and the same dot position
    def __eq__(self, other):
        if not isinstance(other, ElementLR0):
            return False
        return (self.left == other.left and
                self.right == other.right and
                self.point == other.point)

    # Needed so items can be stored in sets
    def __hash__(self):
        return hash((self.left, tuple(self.right), self.point))

    # Pretty print: A -> α • β
    def __str__(self):
        parts = []
        for i, symbol in enumerate(self.right):
            if i == self.point:
                parts.append("•")
            parts.append(str(symbol))
        if self.point == len(self.right):
            parts.append("•")
        return f"{self.left} → {' '.join(parts)}"

    def __repr__(self):
        return self.__str__()