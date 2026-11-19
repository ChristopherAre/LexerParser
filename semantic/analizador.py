# semantic/analizador.py
# FASE 3: Análisis semántico.
# Recorre el AST (patrón Visitor) y verifica:
#   1. Que toda variable esté declarada antes de usarse.
#   2. Que no se declare dos veces la misma variable.
#   3. Que los tipos sean compatibles en asignaciones y operaciones.
#   4. Que las condiciones de 'si' y 'mientras' sean booleanas.
# Al terminar deja la tabla de símbolos {nombre: tipo}.

NUMERICOS = ('entero', 'decimal')


class ErrorSemantico(Exception):
    pass


class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = {}        # {nombre: tipo}

    # ---------------- utilidades ----------------

    def error(self, nodo, mensaje):
        linea = getattr(nodo, 'linea', '?')
        raise ErrorSemantico(f"Error semántico (Línea {linea}): {mensaje}")

    def compatible(self, tipo_destino, tipo_valor):
        """¿Se puede guardar un valor de tipo_valor en una variable tipo_destino?"""
        if tipo_destino == tipo_valor:
            return True
        # Un entero sí cabe en un decimal (5 -> 5.0), al revés no.
        return tipo_destino == 'decimal' and tipo_valor == 'entero'

    def visitar(self, nodo):
        metodo = getattr(self, f'visitar_{type(nodo).__name__}', None)
        if metodo is None:
            raise ErrorSemantico(f"No hay regla semántica para el nodo {type(nodo).__name__}")
        return metodo(nodo)

    def visitar_bloque(self, sentencias):
        for s in sentencias or []:
            self.visitar(s)

    # ---------------- sentencias ----------------

    def visitar_Program(self, nodo):
        self.visitar_bloque(nodo.statements)

    def visitar_VarDecl(self, nodo):
        if nodo.var_name in self.tabla_simbolos:
            self.error(nodo, f"La variable '{nodo.var_name}' ya fue declarada.")
        if nodo.expr is not None:
            tipo_expr = self.visitar(nodo.expr)
            if not self.compatible(nodo.tipo, tipo_expr):
                self.error(nodo, f"No se puede asignar un valor '{tipo_expr}' "
                                 f"a la variable '{nodo.var_name}' de tipo '{nodo.tipo}'.")
        # Se registra DESPUÉS de revisar la expresión: así 'entero x = x;' da error
        self.tabla_simbolos[nodo.var_name] = nodo.tipo

    def visitar_Assign(self, nodo):
        if nodo.var_name not in self.tabla_simbolos:
            self.error(nodo, f"Variable '{nodo.var_name}' no declarada.")
        tipo_var = self.tabla_simbolos[nodo.var_name]
        tipo_expr = self.visitar(nodo.expr)
        if not self.compatible(tipo_var, tipo_expr):
            self.error(nodo, f"Tipos incompatibles en asignación a '{nodo.var_name}': "
                             f"esperado '{tipo_var}', obtenido '{tipo_expr}'.")

    def visitar_Print(self, nodo):
        self.visitar(nodo.expr)          # se puede imprimir cualquier tipo

    def visitar_Read(self, nodo):
        if nodo.var_name not in self.tabla_simbolos:
            self.error(nodo, f"No se puede leer en '{nodo.var_name}': variable no declarada.")

    def visitar_If(self, nodo):
        tipo = self.visitar(nodo.condition)
        if tipo != 'booleano':
            self.error(nodo, f"La condición del 'si' debe ser booleana, se obtuvo '{tipo}'.")
        self.visitar_bloque(nodo.body)
        self.visitar_bloque(nodo.else_body)

    def visitar_While(self, nodo):
        tipo = self.visitar(nodo.condition)
        if tipo != 'booleano':
            self.error(nodo, f"La condición del 'mientras' debe ser booleana, se obtuvo '{tipo}'.")
        self.visitar_bloque(nodo.body)

    # ---------------- expresiones (devuelven su tipo) ----------------

    def visitar_Num(self, nodo):
        return 'decimal' if isinstance(nodo.value, float) else 'entero'

    def visitar_Str(self, nodo):
        return 'cadena'

    def visitar_Bool(self, nodo):
        return 'booleano'

    def visitar_Var(self, nodo):
        if nodo.value not in self.tabla_simbolos:
            self.error(nodo, f"Variable '{nodo.value}' usada sin previa declaración.")
        return self.tabla_simbolos[nodo.value]

    def visitar_UnaryOp(self, nodo):
        tipo = self.visitar(nodo.expr)
        if nodo.op == '-':
            if tipo not in NUMERICOS:
                self.error(nodo, f"El '-' unario solo se aplica a números, no a '{tipo}'.")
            return tipo
        # 'no'
        if tipo != 'booleano':
            self.error(nodo, f"El operador 'no' necesita un booleano, se obtuvo '{tipo}'.")
        return 'booleano'

    def visitar_BinOp(self, nodo):
        izq = self.visitar(nodo.left)
        der = self.visitar(nodo.right)
        op = nodo.op

        # Aritméticos
        if op in ('+', '-', '*', '/'):
            if op == '+' and izq == 'cadena' and der == 'cadena':
                return 'cadena'                     # concatenación
            if izq in NUMERICOS and der in NUMERICOS:
                return 'decimal' if 'decimal' in (izq, der) else 'entero'
            self.error(nodo, f"Operación aritmética '{op}' inválida entre '{izq}' y '{der}'.")

        # Relacionales de orden
        if op in ('<', '>', '<=', '>='):
            if izq in NUMERICOS and der in NUMERICOS:
                return 'booleano'
            self.error(nodo, f"No se puede comparar '{izq}' {op} '{der}': se necesitan números.")

        # Igualdad
        if op in ('==', '!='):
            if izq == der or (izq in NUMERICOS and der in NUMERICOS):
                return 'booleano'
            self.error(nodo, f"No se puede comparar '{izq}' {op} '{der}'.")

        # Lógicos
        if op in ('y', 'o'):
            if izq == 'booleano' and der == 'booleano':
                return 'booleano'
            self.error(nodo, f"El operador '{op}' necesita booleanos, se obtuvo '{izq}' y '{der}'.")

        self.error(nodo, f"Operador desconocido '{op}'.")