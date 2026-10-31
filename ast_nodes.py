# ast_nodes.py

class AST:
    pass

class Program(AST):
    def __init__(self, statements):
        self.statements = statements
    def __repr__(self):
        return f"Program({self.statements})"

class Assign(AST):
    def __init__(self, var_name, expr):
        self.var_name = var_name
        self.expr = expr
    def __repr__(self):
        return f"Assign({self.var_name} = {self.expr})"

class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"

class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value
    def __repr__(self):
        return f"Num({self.value})"

class Var(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value
    def __repr__(self):
        return f"Var({self.value})"

class If(AST):
    def __init__(self, condition, body, else_body=None):
        self.condition = condition
        self.body = body
        self.else_body = else_body
    def __repr__(self):
        return f"If({self.condition}, Body: {self.body}, Else: {self.else_body})"

class While(AST):
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
    def __repr__(self):
        return f"While({self.condition}, Body: {self.body})"