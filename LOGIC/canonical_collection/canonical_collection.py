from .elementLR0 import ElementLR0

class Canonical_Collection:
    # Builds the canonical collection of LR(0) items for a grammar.
    def __init__(self, grammar, end_symbol_name="$"):
        self.grammar = grammar
        self.end_symbol_name = end_symbol_name

        self.states = []          # C = {I0, I1, ...}
        self.transitions = []     # Lista de tuplas (origen, símbolo, destino)
        self.acceptation = set()  # Índices de estados de aceptación

    # 1. Algoritmo de Cerradura (tal cual la diapositiva)

    def cerradura(self, I):
        """
        Entrada: Un conjunto de elementos (I)
        Salida: Regresa un conjunto de elementos.
        """
        I = list(I)
        
        # hacer
        changed = True
        while changed:
            changed = False
            
            # for cada elemento [A -> α•Bβ] en I and B es no terminal
            for item in list(I):
                B = item.symbol_next_point()
                
                if B is not None and not B.is_terminal:
                    # for cada producción B -> γ del conjunto de reglas
                    for production in self.grammar.get_production(B):
                        # Si B -> •γ no se encuentre en I
                        new_item = ElementLR0(production.left, production.right, 0)
                        
                        if new_item not in I:
                            # Añadir B -> •γ a I
                            I.append(new_item)
                            changed = True
                            
        # mientras haya elementos por añadir a I
        # return I
        return I

    # Alias por compatibilidad con el código anterior
    closure = cerradura

    # 2. Algoritmo Ir_a (tal cual la diapositiva)

    def ir_a(self, I, X):
        """
        Entrada: conjunto de elementos de un estado I.
        Salida: cerradura de ese conjunto de elementos.
        """
        J = []  # J := {} // conjunto de elementos vacío
        
        # para cada elemento [A -> α•Xβ] que esté en I
        for item in I:
            next_symbol = item.symbol_next_point()
            
            if next_symbol is not None and next_symbol == X:
                # agregar un elemento [A -> αX•β] en J
                J.append(item.advance_the_point())
                
        # return cerradura(J)
        return self.cerradura(J)

    # Alias por compatibilidad con el código anterior
    go_to = ir_a

    # 3. Algoritmo de Colección Canónica (tal cual la diapositiva)

    def canonical_collection(self):
        """
        coleccionCanonica(G')
        """
        # C := { I0 := cerradura({[S' -> •S$]}) }
        initial_production = self.grammar.productions[0]
        initial_item = ElementLR0(
            initial_production.left,
            initial_production.right,
            0
        )
        I0 = self.cerradura([initial_item])
        self.states = [I0]

        processed = 0
        
        # hacer ... mientras haya más conjuntos de elementos a añadir
        while processed < len(self.states):
            
            # para cada conjunto de elementos de Ii en C
            Ii = self.states[processed]
            
            # para cada símbolo gramatical •X, de cada elemento del conjunto Ii
            symbols = set()
            for item in Ii:
                X = item.symbol_next_point()
                if X is not None:
                    symbols.add(X)
                    
            for X in symbols:
                # si X es $ entonces
                if str(X) == self.end_symbol_name:
                    # Ir_a(Ii, X) := aceptación
                    J = self.ir_a(Ii, X)
                    if J:
                        target = self.find_state(J)
                        
                        # Si el estado no existe, lo creamos
                        if target == -1:
                            self.states.append(J)
                            target = len(self.states) - 1
                            self.transitions.append((processed, X, target))
                        else:
                            # Ya existe, solo aseguramos la transición
                            if (processed, X, target) not in self.transitions:
                                self.transitions.append((processed, X, target))
                        
                        # Marcamos el destino como estado de aceptación
                        self.acceptation.add(target)
                        
                # sino
                else:
                    # evaluamos Ir_a(Ii, X)
                    J = self.ir_a(Ii, X)
                    
                    # si (Ir_a(Ii, X) no está vacío y no está en C) entonces
                    if J:
                        target = self.find_state(J)
                        
                        # Si no está en C (target == -1)
                        if target == -1:
                            # Añadir a C:={Ii+1 := Ir_a (Ii, X)}, como un nuevo estado Ii+1
                            self.states.append(J)
                            target = len(self.states) - 1
                            self.transitions.append((processed, X, target))
                        else:
                            # Si ya estaba en C, solo registramos la transición (si no existe)
                            if (processed, X, target) not in self.transitions:
                                self.transitions.append((processed, X, target))
                                
            processed += 1
            
        return self.states

    # Helpers

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