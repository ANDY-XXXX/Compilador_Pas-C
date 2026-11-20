from LOGIC.syntactic_analysis.lr_parser import LRParser, ParseResult, ParseStep, ParseNode
from LOGIC.syntactic_analysis.lr_table import ActionType

# Terminales cuyo valor léxico se convierte a número.
INT_TERMINALS = ("nint", "num", "entero", "int")
FLOAT_TERMINALS = ("nfloat", "realnum", "real", "float")


def _with_value(symbol, attrs):
    """Símbolo con su valor, como en la corrida del profesor: nint.3, E.14."""
    if not attrs:
        return str(symbol)
    if "valex" in attrs:
        value = attrs["valex"]
        # Solo los tokens con valor léxico propio (id.a, nint.3); '+' queda '+'.
        return str(symbol) if str(value) == str(symbol) else f"{symbol}.{value}"
    if attrs.get("v") is not None:
        return f"{symbol}.{attrs['v']}"
    return str(symbol)


def _format_stack(state_stack, symbol_stack, semantic_stack=None):
    parts = []
    for i, state in enumerate(state_stack):
        parts.append(str(state))
        if i < len(symbol_stack):
            attrs = semantic_stack[i] if semantic_stack and i < len(semantic_stack) else None
            parts.append(_with_value(symbol_stack[i], attrs))
    return " ".join(parts)


class AttrDict(dict):
    # Permite escribir E0.v en lugar de E0['v']; un atributo inexistente vale None.
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__


class SemanticParser(LRParser):
    def __init__(self, table, tokens, positions=None):
        super().__init__(table, tokens)
        self.semantic_stack = []
        # (línea, columna) de cada token, para ubicar los errores.
        self.positions = list(positions or [])
        self.semantic_errors = []

    def _where(self, index):
        if index < len(self.positions):
            line, column = self.positions[index]
            return f"Línea {line}, columna {column}: "
        return ""

    def parse(self):
        state_stack = [0]
        symbol_stack = []
        node_stack = []
        derivation = []
        self.semantic_stack = []
        self.semantic_errors = []
        index = 0
        steps = []
        step = 0

        # Pila con estado + símbolo.valor (ej. 0 E.3 1 + 6 nint.2 5)
        def fmt_stack(): return _format_stack(state_stack, symbol_stack, self.semantic_stack)

        # Entrada con valor léxico solo en los tokens que lo tienen (ej. nint.3 + nint.4 $)
        def fmt_input():
            return " ".join(
                f"{t[1]}.{t[0]}" if t[1] != "$" and t[0] != t[1] else t[1]
                for t in self.tokens[index:]
            )

        while step < 10000:
            step += 1
            current_state = state_stack[-1]

            if index >= len(self.tokens):
                steps.append(ParseStep(step, fmt_stack(), fmt_input(), "ERROR: Fin de entrada inesperado"))
                return ParseResult(False, steps, derivation, None, "Fin de entrada inesperado")

            lexeme, terminal = self.tokens[index]
            action = self.table.action.get((current_state, terminal))

            # Pila y entrada se toman ANTES de aplicar la acción.
            stack_before = fmt_stack()
            input_before = fmt_input()

            if action is None:
                steps.append(ParseStep(step, stack_before, input_before, f"ERROR: sin acción para '{terminal}'"))
                return ParseResult(
                    False, steps, derivation, None,
                    f"{self._where(index)}Error sintáctico: no se esperaba '{lexeme}' "
                    f"(terminal '{terminal}') en el estado I{current_state}.",
                )

            if action.type == ActionType.SHIFT:
                # Formato en el desplazamiento: d5 : nint.3
                accion_str = f"d{action.target} : {_with_value(terminal, {'valex': lexeme})}"

                val = lexeme
                try:
                    if terminal in INT_TERMINALS: val = int(lexeme)
                    elif terminal in FLOAT_TERMINALS: val = float(lexeme)
                except ValueError: pass

                self.semantic_stack.append({'valex': val})
                symbol_stack.append(terminal)
                state_stack.append(action.target)
                node_stack.append(ParseNode(_with_value(terminal, {'valex': lexeme}), is_terminal=True))
                steps.append(ParseStep(step, stack_before, input_before, accion_str))
                index += 1

            elif action.type == ActionType.REDUCE:
                prod = self.table.grammar.productions[action.production]
                right_len = len(prod.right)
                nt = str(prod.left)

                popped_vals = self.semantic_stack[-right_len:] if right_len > 0 else []
                children = node_stack[-right_len:] if right_len > 0 else []

                if right_len:
                    del self.semantic_stack[-right_len:]
                    del state_stack[-right_len:]
                    del symbol_stack[-right_len:]
                    del node_stack[-right_len:]

                result_attrs = {}
                action_str = getattr(self.table.grammar, 'actions', {}).get(action.production, "")
                semantic_error = None

                if action_str:
                    # Creamos un entorno para evaluar la acción semántica:
                    # E1, E2… son las apariciones del lado derecho; E0 es el lado izquierdo.
                    # Sin número, un símbolo que aparece una sola vez a la derecha
                    # se refiere a esa aparición; el del lado izquierdo, a E0.
                    env = {}
                    counts = {}
                    names = [str(sym) for sym in prod.right]
                    for i, sym_name in enumerate(names):
                        counts[sym_name] = counts.get(sym_name, 0) + 1
                        var_name = f"{sym_name}{counts[sym_name]}"
                        env[var_name] = AttrDict(popped_vals[i])

                        if names.count(sym_name) == 1:
                            env[sym_name] = env[var_name]

                    lhs_name = f"{nt}0"
                    env[lhs_name] = AttrDict()
                    env[nt] = env[lhs_name]

                    try:
                        # Se acepta tanto '=' como ':=' (notación de clase).
                        exec(action_str.replace(":=", "="), {}, env)
                        result_attrs = dict(env[lhs_name])
                    except Exception as e:
                        semantic_error = f"{self._where(index)}Error en la acción {{{action_str}}} de {prod}: {e}"
                        self.semantic_errors.append(semantic_error)
                        result_attrs = {}

                self.semantic_stack.append(result_attrs)
                symbol_stack.append(nt)
                derivation.append(str(prod))
                node_stack.append(ParseNode(_with_value(nt, result_attrs), children=children))

                goto_target = self.table.goto.get((state_stack[-1], nt))
                if goto_target is None:
                    steps.append(ParseStep(step, stack_before, input_before, f"ERROR GOTO con {nt}"))
                    return ParseResult(False, steps, derivation, None, f"Error GOTO con {nt}")
                state_stack.append(goto_target)

                # Formato en la reducción: r7 : F -> nint {F.v = nint.valex} [= 3]
                prod_str = str(prod)
                semantic_part = f" {{{action_str}}}" if action_str else ""
                if semantic_error:
                    val_display = " [ERROR semántico]"
                elif result_attrs.get('v') is not None:
                    val_display = f" [= {result_attrs['v']}]"
                elif result_attrs:
                    val_display = " [" + ", ".join(f"{k} = {v}" for k, v in result_attrs.items()) + "]"
                else:
                    val_display = ""

                accion_str = f"r{action.production + 1} : {prod_str}{semantic_part}{val_display}"
                steps.append(ParseStep(step, stack_before, input_before, accion_str))

            elif action.type == ActionType.ACCEPT:
                steps.append(ParseStep(step, stack_before, input_before, "ACEPTAR"))
                final_val = self.semantic_stack[-1].get('v', '') if self.semantic_stack else ""
                root = node_stack[-1] if len(node_stack) == 1 else ParseNode("<programa>", children=list(node_stack))
                return ParseResult(True, steps, derivation, root, final_value=final_val)

            else:
                steps.append(ParseStep(step, stack_before, input_before, f"ERROR: Tipo de acción desconocido {action.type}"))
                return ParseResult(False, steps, derivation, None, "Error interno: tipo de acción desconocido")

        return ParseResult(False, steps, derivation, None, "Bucle infinito")