# ast_nodes.py
# Nodos del Árbol de Sintaxis Abstracta (AST).
# Todos los nodos guardan "linea" para reportar errores semánticos y de ejecución.


class AST:
    pass


class Program(AST):
    def __init__(self, statements):
        self.statements = statements

    def __repr__(self):
        return f"Program({self.statements})"


# ---------------- Sentencias ----------------

class VarDecl(AST):
    """entero x = 5;   o   entero x;"""
    def __init__(self, tipo, var_name, expr, linea):
        self.tipo = tipo            # 'entero', 'decimal', 'cadena', 'booleano'
        self.var_name = var_name
        self.expr = expr            # puede ser None si no se inicializa
        self.linea = linea

    def __repr__(self):
        return f"VarDecl({self.tipo} {self.var_name} = {self.expr})"


class Assign(AST):
    """x = x + 1;"""
    def __init__(self, var_name, expr, linea):
        self.var_name = var_name
        self.expr = expr
        self.linea = linea

    def __repr__(self):
        return f"Assign({self.var_name} = {self.expr})"


class Print(AST):
    """imprimir(expr);"""
    def __init__(self, expr, linea):
        self.expr = expr
        self.linea = linea

    def __repr__(self):
        return f"Print({self.expr})"


class Read(AST):
    """leer(x);"""
    def __init__(self, var_name, linea):
        self.var_name = var_name
        self.linea = linea

    def __repr__(self):
        return f"Read({self.var_name})"


class If(AST):
    """si (cond) { ... } sino { ... }"""
    def __init__(self, condition, body, else_body, linea):
        self.condition = condition
        self.body = body
        self.else_body = else_body  # lista de sentencias o None
        self.linea = linea

    def __repr__(self):
        return f"If({self.condition}, Body: {self.body}, Else: {self.else_body})"


class While(AST):
    """mientras (cond) { ... }"""
    def __init__(self, condition, body, linea):
        self.condition = condition
        self.body = body
        self.linea = linea

    def __repr__(self):
        return f"While({self.condition}, Body: {self.body})"


# ---------------- Expresiones ----------------

class BinOp(AST):
    """a + b,  a < b,  a y b ..."""
    def __init__(self, left, op, right, linea):
        self.left = left
        self.op = op
        self.right = right
        self.linea = linea

    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"


class UnaryOp(AST):
    """-x   o   no x"""
    def __init__(self, op, expr, linea):
        self.op = op                # '-' o 'no'
        self.expr = expr
        self.linea = linea

    def __repr__(self):
        return f"UnaryOp({self.op} {self.expr})"


class Num(AST):
    """Número entero o decimal."""
    def __init__(self, token):
        self.token = token
        self.value = token.value
        self.linea = token.linea

    def __repr__(self):
        return f"Num({self.value})"


class Str(AST):
    """Cadena "hola"."""
    def __init__(self, token):
        self.token = token
        self.value = token.value
        self.linea = token.linea

    def __repr__(self):
        return f'Str("{self.value}")'


class Bool(AST):
    """verdadero / falso."""
    def __init__(self, token):
        self.token = token
        self.value = (token.value == 'verdadero')
        self.linea = token.linea

    def __repr__(self):
        return f"Bool({'verdadero' if self.value else 'falso'})"


class Var(AST):
    """Uso de una variable dentro de una expresión."""
    def __init__(self, token):
        self.token = token
        self.value = token.value
        self.linea = token.linea

    def __repr__(self):
        return f"Var({self.value})"