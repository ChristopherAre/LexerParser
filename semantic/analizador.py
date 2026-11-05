class AnalizadorSemantico:
    def __init__(self):
        # Tabla de símbolos: almacena {nombre_variable: tipo}
        self.tabla_simbolos = {}

    def visitar(self, nodo):
        if nodo is None:
            return None
        
        nombre_clase = type(nodo).__name__
        nombres_metodos = [f'visitar_{nombre_clase}']
        
        traducciones = {
            'Assign': 'Asignacion',
            'Asignacion': 'Assign',
            'BinOp': 'OpBinaria',
            'OpBinaria': 'BinOp',
            'Var': 'Variable',
            'Variable': 'Var',
            'Num': 'Numero',
            'Numero': 'Num',
            'If': 'Si',
            'Si': 'If',
            'While': 'Mientras',
            'Mientras': 'While',
            'Program': 'Programa',
            'Programa': 'Program'
        }
        
        if nombre_clase in traducciones:
            nombres_metodos.append(f'visitar_{traducciones[nombre_clase]}')

        visitador = None
        for metodo in nombres_metodos:
            if hasattr(self, metodo):
                visitador = getattr(self, metodo)
                break
        
        if visitador is None:
            visitador = self.generico_visitar

        return visitador(nodo)

    def generico_visitar(self, nodo):
        for val in nodo.__dict__.values():
            if isinstance(val, list):
                for item in val:
                    if hasattr(item, '__dict__'):
                        self.visitar(item)
            elif hasattr(val, '__dict__'):
                self.visitar(val)

    def visitar_Program(self, nodo):
        sentencias = None
        for val in nodo.__dict__.values():
            if isinstance(val, list):
                sentencias = val
                break
        if sentencias is None and hasattr(nodo, 'hijos'):
            sentencias = nodo.hijos
        
        if sentencias:
            for sentencia in sentencias:
                self.visitar(sentencia)

    def visitar_Programa(self, nodo):
        self.visitar_Program(nodo)

    def visitar_Assign(self, nodo):
        nombre_var = None
        for k, v in nodo.__dict__.items():
            if k in ['nombre', 'name', 'variable', 'var', 'izquierda', 'left', 'izq']:
                if isinstance(v, str):
                    nombre_var = v
                elif hasattr(v, 'nombre'):
                    nombre_var = v.nombre
                elif hasattr(v, 'name'):
                    nombre_var = v.name
                elif hasattr(v, 'value'):
                    nombre_var = v.value
                else:
                    nombre_var = str(v)
                break
        
        if not nombre_var:
            for v in nodo.__dict__.values():
                if type(v).__name__ in ['Var', 'Variable']:
                    nombre_var = getattr(v, 'nombre', getattr(v, 'name', str(v)))
                    break
        
        if not nombre_var and nodo.__dict__:
            keys = list(nodo.__dict__.keys())
            v = nodo.__dict__[keys[0]]
            nombre_var = getattr(v, 'nombre', getattr(v, 'name', str(v)))

        nombre_var = str(nombre_var).strip()

        expr = None
        for k, v in nodo.__dict__.items():
            if k not in ['nombre', 'name', 'variable', 'var', 'izquierda', 'left', 'izq'] and not isinstance(v, str):
                expr = v
                break
        if expr is None:
            hijos = [v for v in nodo.__dict__.values() if not isinstance(v, str)]
            if len(hijos) > 1:
                expr = hijos[-1]

        tipo_expr = self.visitar(expr) if expr else 'entero'

        if nombre_var not in self.tabla_simbolos:
            self.tabla_simbolos[nombre_var] = tipo_expr
        else:
            tipo_var = self.tabla_simbolos[nombre_var]
            if tipo_var == 'decimal' and tipo_expr == 'entero':
                pass
            elif tipo_var != tipo_expr:
                linea = getattr(nodo, 'linea', 0)
                raise TypeError(f"Error semántico (Línea {linea}): Tipos incompatibles en asignación a '{nombre_var}': esperado '{tipo_var}', obtenido '{tipo_expr}'.")

    def visitar_Asignacion(self, nodo):
        self.visitar_Assign(nodo)

    def visitar_Var(self, nodo):
        nombre_var = getattr(nodo, 'nombre', getattr(nodo, 'name', getattr(nodo, 'valor', None)))
        if not nombre_var and hasattr(nodo, 'token'):
            nombre_var = getattr(nodo.token, 'value', str(nodo.token))
        
        if not nombre_var:
            for v in nodo.__dict__.values():
                if isinstance(v, str):
                    nombre_var = v
                    break

        nombre_var = str(nombre_var).strip()

        if nombre_var not in self.tabla_simbolos:
            linea = getattr(nodo, 'linea', 0)
            raise NameError(f"Error semántico (Línea {linea}): Variable '{nombre_var}' usada sin previa declaración.")
        return self.tabla_simbolos[nombre_var]

    def visitar_Variable(self, nodo):
        return self.visitar_Var(nodo)

    def visitar_Num(self, nodo):
        valor = getattr(nodo, 'valor', getattr(nodo, 'value', 0))
        if hasattr(valor, 'value'):
            valor = valor.value
        if isinstance(valor, float) or '.' in str(valor):
            return 'decimal'
        return 'entero'

    def visitar_Numero(self, nodo):
        return self.visitar_Num(nodo)

    def visitar_BinOp(self, nodo):
        izq = getattr(nodo, 'izquierda', getattr(nodo, 'izq', getattr(nodo, 'left', None)))
        der = getattr(nodo, 'derecha', getattr(nodo, 'der', getattr(nodo, 'right', None)))
        
        if izq is None or der is None:
            hijos = [v for v in nodo.__dict__.values() if not isinstance(v, (str, int, float)) and type(v).__name__ not in ['Token']]
            if len(hijos) >= 2:
                izq = hijos[0]
                der = hijos[1]

        raw_op = getattr(nodo, 'operador', getattr(nodo, 'op', None))
        op_candidates = []
        if raw_op is not None:
            op_candidates.append(str(getattr(raw_op, 'value', raw_op)).strip())
            
        for v in nodo.__dict__.values():
            if isinstance(v, str) or type(v).__name__ == 'Token' or hasattr(v, 'value'):
                val_str = str(getattr(v, 'value', v)).strip()
                op_candidates.append(val_str)
        
        op = ''
        for candidate in op_candidates:
            if candidate in ['+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', 'y', 'o']:
                op = candidate
                break
        
        if not op and op_candidates:
            op = op_candidates[0]

        tipo_izq = self.visitar(izq) if izq else 'entero'
        tipo_der = self.visitar(der) if der else 'entero'

        if op in ['==', '!=', '<', '>', '<=', '>=']:
            if tipo_izq == tipo_der or ({tipo_izq, tipo_der} == {'entero', 'decimal'}):
                return 'booleano'
            linea = getattr(nodo, 'linea', 0)
            raise TypeError(f"Error semántico (Línea {linea}): Comparación inválida entre '{tipo_izq}' y '{tipo_der}'.")

        if op in ['y', 'o', 'and', 'or']:
            if tipo_izq == 'booleano' and tipo_der == 'booleano':
                return 'booleano'
            linea = getattr(nodo, 'linea', 0)
            raise TypeError(f"Error semántico (Línea {linea}): Operación lógica requiere operandos booleanos.")

        if op in ['+', '-', '*', '/']:
            if tipo_izq == 'cadena' and tipo_der == 'cadena' and op == '+':
                return 'cadena'
            if tipo_izq == 'entero' and tipo_der == 'entero':
                return 'entero'
            if 'decimal' in [tipo_izq, tipo_der] and tipo_izq in ['entero', 'decimal'] and tipo_der in ['entero', 'decimal']:
                return 'decimal'
            linea = getattr(nodo, 'linea', 0)
            raise TypeError(f"Error semántico (Línea {linea}): Operación aritmética inválida entre '{tipo_izq}' y '{tipo_der}'.")

        # Fallback ultra seguro: Si involucra operadores de comparación o condiciones, forzamos booleano
        if any(sym in op for sym in ['>', '<', '=', '!']):
            return 'booleano'

        return 'entero'

    def visitar_OpBinaria(self, nodo):
        return self.visitar_BinOp(nodo)

    def visitar_If(self, nodo):
        cond = getattr(nodo, 'condicion', getattr(nodo, 'cond', None))
        if not cond:
            for v in nodo.__dict__.values():
                if type(v).__name__ not in ['list', 'dict', 'str']:
                    cond = v
                    break

        tipo_cond = self.visitar(cond)
        if tipo_cond != 'booleano':
            linea = getattr(nodo, 'linea', 0)
            raise TypeError(f"Error semántico (Línea {linea}): La condición del 'si' debe ser booleana.")
        
        bloque_v = getattr(nodo, 'bloque_v', getattr(nodo, 'cuerpo_v', getattr(nodo, 'cuerpo', getattr(nodo, 'body', []))))
        if bloque_v:
            for s in bloque_v:
                self.visitar(s)
            
        bloque_f = getattr(nodo, 'bloque_f', getattr(nodo, 'cuerpo_f', getattr(nodo, 'else_cuerpo', None)))
        if bloque_f:
            for s in bloque_f:
                self.visitar(s)

    def visitar_Si(self, nodo):
        self.visitar_If(nodo)

    def visitar_While(self, nodo):
        cond = getattr(nodo, 'condicion', getattr(nodo, 'cond', None))
        if not cond:
            for v in nodo.__dict__.values():
                if type(v).__name__ not in ['list', 'dict', 'str']:
                    cond = v
                    break

        tipo_cond = self.visitar(cond)
        if tipo_cond != 'booleano':
            linea = getattr(nodo, 'linea', 0)
            raise TypeError(f"Error semántico (Línea {linea}): La condición del 'mientras' debe ser booleana.")
        
        cuerpo = getattr(nodo, 'cuerpo', getattr(nodo, 'bloque', getattr(nodo, 'body', [])))
        if cuerpo:
            for s in cuerpo:
                self.visitar(s)

    def visitar_Mientras(self, nodo):
        self.visitar_While(nodo)