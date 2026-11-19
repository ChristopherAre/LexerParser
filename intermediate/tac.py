# intermediate/tac.py
# FASE 4: Generador de código intermedio de tres direcciones (TAC).
#
# Recorre el AST ya validado por la semántica y lo traduce a instrucciones
# que hacen UNA sola operación cada una:
#
#     (operacion, argumento1, argumento2, destino)
#
# Ejemplo:  entero x = 5 + 3 * 2;
#     ('*',      '3',   '2',   '@t1')     @t1 = 3 * 2
#     ('+',      '5',   '@t1', '@t2')     @t2 = 5 + @t1
#     ('ASSIGN', '@t2', None,  'x')       x = @t2
#
# Temporales: @t1, @t2...   Etiquetas: @L1, @L2...
# Empiezan con @ para que nunca choquen con una variable del programa.
#
# Cómo se escriben los literales:
#     entero -> '5'     decimal -> '3.14'     cadena -> '"hola"'     booleano -> '1' / '0'

from ast_nodes import (Program, VarDecl, Assign, Print, Read, If, While,
                       BinOp, UnaryOp, Num, Str, Bool, Var)

# Valor inicial de una variable declarada sin '=' (entero z;)
VALOR_INICIAL = {'entero': '0', 'decimal': '0.0', 'cadena': '""', 'booleano': '0'}


class GeneradorTAC:
    def __init__(self):
        self.instrucciones = []
        self.conteo_temp = 0
        self.conteo_etiquetas = 0
        self.tipos = {}             # tipo de cada variable (lo usa 'leer')

    # ---------------- infraestructura ----------------

    def nuevo_temp(self):
        self.conteo_temp += 1
        return f'@t{self.conteo_temp}'

    def nueva_etiqueta(self):
        self.conteo_etiquetas += 1
        return f'@L{self.conteo_etiquetas}'

    def emitir(self, op, arg1=None, arg2=None, res=None):
        self.instrucciones.append((op, arg1, arg2, res))

    def generar(self, nodo):
        metodo = getattr(self, f'generar_{type(nodo).__name__}', None)
        if metodo is None:
            raise NotImplementedError(f"TAC no soporta el nodo {type(nodo).__name__}")
        metodo(nodo)
        return self.instrucciones

    def generar_bloque(self, sentencias):
        for s in sentencias or []:
            self.generar(s)

    # ---------------- sentencias ----------------

    def generar_Program(self, nodo):
        self.generar_bloque(nodo.statements)

    def generar_VarDecl(self, nodo):
        self.tipos[nodo.var_name] = nodo.tipo
        if nodo.expr is not None:
            fuente = self.evaluar_expr(nodo.expr)
        else:
            fuente = VALOR_INICIAL[nodo.tipo]
        self.emitir('ASSIGN', fuente, None, nodo.var_name)

    # TAC 1 - Asignación: calcular la expresión y copiarla a la variable
    def generar_Assign(self, nodo):
        fuente = self.evaluar_expr(nodo.expr)
        self.emitir('ASSIGN', fuente, None, nodo.var_name)

    # TAC 2 - Imprimir: calcular la expresión y emitir PRINT
    def generar_Print(self, nodo):
        fuente = self.evaluar_expr(nodo.expr)
        self.emitir('PRINT', fuente)

    # Extensión: leer(x) -> READ tipo -> x
    def generar_Read(self, nodo):
        tipo = self.tipos.get(nodo.var_name, 'entero')
        self.emitir('READ', tipo, None, nodo.var_name)

    # TAC 3 - Si
    #   Sin sino:                   Con sino:
    #     cond -> @t                  cond -> @t
    #     JMP_FALSE @t  @Lfin         JMP_FALSE @t  @Lsino
    #     ...bloque...                ...bloque si...
    #     LABEL @Lfin                 JMP @Lfin
    #                                 LABEL @Lsino
    #                                 ...bloque sino...
    #                                 LABEL @Lfin
    def generar_If(self, nodo):
        cond = self.evaluar_expr(nodo.condition)
        if nodo.else_body is None:
            fin = self.nueva_etiqueta()
            self.emitir('JMP_FALSE', cond, None, fin)
            self.generar_bloque(nodo.body)
            self.emitir('LABEL', None, None, fin)
        else:
            sino = self.nueva_etiqueta()
            fin = self.nueva_etiqueta()
            self.emitir('JMP_FALSE', cond, None, sino)
            self.generar_bloque(nodo.body)
            self.emitir('JMP', None, None, fin)
            self.emitir('LABEL', None, None, sino)
            self.generar_bloque(nodo.else_body)
            self.emitir('LABEL', None, None, fin)

    # TAC 4 - Mientras
    #   LABEL @Linicio
    #   cond -> @t                (dentro del ciclo: se recalcula en cada vuelta)
    #   JMP_FALSE @t  @Lfin
    #   ...bloque...
    #   JMP @Linicio
    #   LABEL @Lfin
    def generar_While(self, nodo):
        inicio = self.nueva_etiqueta()
        fin = self.nueva_etiqueta()
        self.emitir('LABEL', None, None, inicio)
        cond = self.evaluar_expr(nodo.condition)
        self.emitir('JMP_FALSE', cond, None, fin)
        self.generar_bloque(nodo.body)
        self.emitir('JMP', None, None, inicio)
        self.emitir('LABEL', None, None, fin)

    # ---------------- expresiones ----------------

    # TAC 5 - Evaluar expresión: devuelve el nombre donde queda el resultado
    #   literal  -> el literal mismo ('5', '"hola"', '1')
    #   variable -> su nombre
    #   operación -> primero sus partes (recursión) y luego un temporal nuevo
    def evaluar_expr(self, nodo):
        if isinstance(nodo, Num):
            return str(nodo.value)
        if isinstance(nodo, Str):
            return f'"{nodo.value}"'
        if isinstance(nodo, Bool):
            return '1' if nodo.value else '0'
        if isinstance(nodo, Var):
            return nodo.value
        if isinstance(nodo, UnaryOp):
            arg = self.evaluar_expr(nodo.expr)
            temp = self.nuevo_temp()
            self.emitir('NEG' if nodo.op == '-' else 'NO', arg, None, temp)
            return temp
        if isinstance(nodo, BinOp):
            izq = self.evaluar_expr(nodo.left)
            der = self.evaluar_expr(nodo.right)
            temp = self.nuevo_temp()
            self.emitir(nodo.op, izq, der, temp)
            return temp
        raise NotImplementedError(f"Expresión no soportada: {type(nodo).__name__}")


def imprimir_tac(instrucciones):
    """Muestra el TAC como tabla numerada."""
    print(f"{'#':>3} | {'OP':<10} | {'ARG1':<10} | {'ARG2':<10} | {'RES':<10}")
    print('-' * 54)
    for i, (op, a1, a2, res) in enumerate(instrucciones):
        print(f"{i:03} | {op:<10} | {a1 or '':<10} | {a2 or '':<10} | {res or '':<10}")