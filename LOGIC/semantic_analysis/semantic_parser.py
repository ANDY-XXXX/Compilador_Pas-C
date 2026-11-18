from LOGIC.syntactic_analysis.lr_parser import LRParser, ParseResult, ParseStep
from LOGIC.syntactic_analysis.lr_table import ActionType

def _format_stack(state_stack, symbol_stack):
    parts = []
    for i, state in enumerate(state_stack):
        parts.append(str(state))
        if i < len(symbol_stack):
            parts.append(str(symbol_stack[i]))
    return " ".join(parts)

class SemanticParser(LRParser):
    def __init__(self, table, tokens):
        super().__init__(table, tokens)
        self.semantic_stack = []

    def parse(self):
        state_stack = [0]
        symbol_stack = []
        self.semantic_stack = []
        index = 0
        steps = []
        step = 0

        # Ahora mostramos estado + símbolos en la pila (ej. 0 nint 5)
        def fmt_stack(): return _format_stack(state_stack, symbol_stack)
        
        # Ahora mostramos el tipo de token junto con su valor léxico (ej. nint.3 + nint.4 $)
        def fmt_input(): 
            return " ".join(
                f"{t[1]}.{t[0]}" if t[1] != "$" else "$" 
                for t in self.tokens[index:]
            )

        while step < 10000:
            step += 1
            current_state = state_stack[-1]
            
            if index >= len(self.tokens):
                steps.append(ParseStep(step, fmt_stack(), fmt_input(), "ERROR: Fin de entrada inesperado"))
                return ParseResult(False, steps, [], None, "Fin de entrada inesperado")

            lexeme, terminal = self.tokens[index]
            action = self.table.action.get((current_state, terminal))

            if action is None:
                steps.append(ParseStep(step, fmt_stack(), fmt_input(), f"ERROR: sin acción para '{terminal}'"))
                return ParseResult(False, steps, [], None, f"Error sintáctico en '{terminal}'")

            if action.type == ActionType.SHIFT:
                # Formato en el desplazamiento: d5 : nint.3
                accion_str = f"d{action.target} : {terminal}.{lexeme}"
                
                val = lexeme
                try:
                    if terminal in ("nint", "num", "entero", "int"): val = int(lexeme)
                    elif terminal in ("nfloat", "realnum", "real", "float"): val = float(lexeme)
                except: pass
                
                self.semantic_stack.append({'valex': val})
                symbol_stack.append(terminal)
                state_stack.append(action.target)
                steps.append(ParseStep(step, fmt_stack(), fmt_input(), accion_str))
                index += 1

            elif action.type == ActionType.REDUCE:
                prod = self.table.grammar.productions[action.production]
                right_len = len(prod.right)
                nt = str(prod.left)
                
                popped_vals = self.semantic_stack[-right_len:] if right_len > 0 else []
                
                if right_len: 
                    del self.semantic_stack[-right_len:]
                    del state_stack[-right_len:]
                    del symbol_stack[-right_len:]
                
                result_attrs = {}
                action_str = getattr(self.table.grammar, 'actions', {}).get(action.production, "")
                
                if action_str:
                    # Creamos un entorno para evaluar la acción semántica
                    class AttrDict(dict):
                        __getattr__ = dict.get
                        __setattr__ = dict.__setitem__

                    env = {}
                    counts = {}
                    for i, sym in enumerate(prod.right):
                        sym_name = str(sym)
                        counts[sym_name] = counts.get(sym_name, 0) + 1
                        var_name = f"{sym_name}{counts[sym_name]}"
                        env[var_name] = AttrDict(popped_vals[i])
                        
                        if str(prod.right).count(sym_name) == 1:
                            env[sym_name] = env[var_name]

                    lhs_name = f"{nt}0"
                    env[lhs_name] = AttrDict()
                    env[nt] = env[lhs_name]
                    
                    try:
                        exec(action_str, {}, env)
                        result_attrs = dict(env[lhs_name])
                    except Exception as e:
                        result_attrs = {'v': f"Error acción: {e}"}
                
                self.semantic_stack.append(result_attrs)
                symbol_stack.append(nt)
                
                goto_target = self.table.goto.get((state_stack[-1], nt))
                if goto_target is None:
                    steps.append(ParseStep(step, fmt_stack(), fmt_input(), f"ERROR GOTO con {nt}"))
                    return ParseResult(False, steps, [], None, f"Error GOTO con {nt}")
                state_stack.append(goto_target)
                
                # Formato en la reducción: r3 : F -> nint {F0.v = nint.valex} [Resultado: 3]
                prod_str = str(prod)
                semantic_part = f" {{{action_str}}}" if action_str else ""
                val_display = f" [= {result_attrs.get('v', '')}]" if result_attrs else ""
                
                accion_str = f"r{action.production + 1} : {prod_str}{semantic_part}{val_display}"
                steps.append(ParseStep(step, fmt_stack(), fmt_input(), accion_str))

            elif action.type == ActionType.ACCEPT:
                steps.append(ParseStep(step, fmt_stack(), fmt_input(), "ACEPTAR"))
                final_val = self.semantic_stack[-1].get('v', '') if self.semantic_stack else ""
                return ParseResult(True, steps, [], None, final_value=final_val)
                
            else:
                steps.append(ParseStep(step, fmt_stack(), fmt_input(), f"ERROR: Tipo de acción desconocido {action.type}"))
                return ParseResult(False, steps, [], None, "Error interno: tipo de acción desconocido")
        
        return ParseResult(False, steps, [], None, "Bucle infinito")