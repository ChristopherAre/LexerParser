# parser/parser.py
from lexer.lexer import Lexer
from ast_nodes import Program, Assign, BinOp, Num, Var, If, While

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self, message="Error sintáctico"):
        raise Exception(f"{message}: Token inesperado '{self.current_token.type}' (valor: {self.current_token.value})")

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Se esperaba {token_type}")

    def factor(self):
        token = self.current_token
        if token.type == 'INT' or token.type == 'FLOAT':
            self.eat(token.type)
            return Num(token)
        elif token.type == 'ID':
            self.eat('ID')
            return Var(token)
        elif token.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.expr()
            self.eat('RPAREN')
            return node
        else:
            self.error("Factor inválido")

    def term(self):
        node = self.factor()
        while self.current_token.type in ('MUL', 'DIV'):
            token = self.current_token
            if token.type == 'MUL':
                self.eat('MUL')
            elif token.type == 'DIV':
                self.eat('DIV')
            node = BinOp(left=node, op=token.value, right=self.factor())
        return node

    def expr(self):
        node = self.term()
        while self.current_token.type in ('PLUS', 'MINUS', 'LT', 'GT', 'EQ'):
            token = self.current_token
            if token.type == 'PLUS':
                self.eat('PLUS')
            elif token.type == 'MINUS':
                self.eat('MINUS')
            elif token.type == 'LT':
                self.eat('LT')
            elif token.type == 'GT':
                self.eat('GT')
            elif token.type == 'EQ':
                self.eat('EQ')
            node = BinOp(left=node, op=token.value, right=self.term())
        return node

    def statement(self):
        if self.current_token.type == 'ID':
            var_name = self.current_token.value
            self.eat('ID')
            self.eat('ASSIGN')
            node = Assign(var_name, self.expr())
            self.eat('SEMI')
            return node
        elif self.current_token.type == 'IF':
            self.eat('IF')
            self.eat('LPAREN')
            condition = self.expr()
            self.eat('RPAREN')
            self.eat('LBRACE')
            body = []
            while self.current_token.type != 'RBRACE' and self.current_token.type != 'EOF':
                body.append(self.statement())
            self.eat('RBRACE')
            
            else_body = None
            if self.current_token.type == 'ELSE':
                self.eat('ELSE')
                self.eat('LBRACE')
                else_body = []
                while self.current_token.type != 'RBRACE' and self.current_token.type != 'EOF':
                    else_body.append(self.statement())
                self.eat('RBRACE')
            return If(condition, body, else_body)
        elif self.current_token.type == 'WHILE':
            self.eat('WHILE')
            self.eat('LPAREN')
            condition = self.expr()
            self.eat('RPAREN')
            self.eat('LBRACE')
            body = []
            while self.current_token.type != 'RBRACE' and self.current_token.type != 'EOF':
                body.append(self.statement())
            self.eat('RBRACE')
            return While(condition, body)
        else:
            self.error("Sentencia inválida")

    def parse(self):
        statements = []
        while self.current_token.type != 'EOF':
            statements.append(self.statement())
        return Program(statements)