# parser/parser.py
# FASE 2: Parser descendente recursivo. Valida la gramática y construye el AST.
#
# Gramática (de menor a mayor precedencia en las expresiones):
#
#   programa    -> sentencia* EOF
#   sentencia   -> declaracion | asignacion | imprimir | leer | si | mientras
#   declaracion -> TIPO ID ( '=' expr )? ';'
#   asignacion  -> ID '=' expr ';'
#   imprimir    -> 'imprimir' '(' expr ')' ';'
#   leer        -> 'leer' '(' ID ')' ';'
#   si          -> 'si' '(' expr ')' bloque ( 'sino' ( si | bloque ) )?
#   mientras    -> 'mientras' '(' expr ')' bloque
#   bloque      -> '{' sentencia* '}'
#
#   expr        -> o_logico
#   o_logico    -> y_logico ( 'o' y_logico )*
#   y_logico    -> comparacion ( 'y' comparacion )*
#   comparacion -> suma ( RELOP suma )?          <  >  <=  >=  ==  !=
#   suma        -> termino ( ('+' | '-') termino )*
#   termino     -> unario ( ('*' | '/') unario )*
#   unario      -> ('-' | 'no') unario | factor
#   factor      -> INT | FLOAT | STRING | BOOL | ID | '(' expr ')'

from ast_nodes import (Program, VarDecl, Assign, Print, Read, If, While,
                       BinOp, UnaryOp, Num, Str, Bool, Var)

TIPOS = ('ENTERO', 'DECIMAL', 'CADENA', 'BOOLEANO')

NOMBRES = {
    'SEMI': "';'", 'LPAREN': "'('", 'RPAREN': "')'", 'LBRACE': "'{'",
    'RBRACE': "'}'", 'ASSIGN': "'='", 'ID': 'un identificador', 'EOF': 'fin de archivo',
}


class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    # ---------------- utilidades ----------------

    def error(self, message="Error sintáctico"):
        tok = self.current_token
        valor = 'fin de archivo' if tok.type == 'EOF' else f"'{tok.value}'"
        raise Exception(f"Error sintáctico (Línea {tok.linea}): {message}, se encontró {valor}")

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error(f"Se esperaba {NOMBRES.get(token_type, token_type)}")

    # ---------------- programa y sentencias ----------------

    def parse(self):
        statements = []
        while self.current_token.type != 'EOF':
            statements.append(self.statement())
        return Program(statements)

    def statement(self):
        tipo = self.current_token.type
        if tipo in TIPOS:
            return self.declaracion()
        if tipo == 'ID':
            return self.asignacion()
        if tipo == 'IMPRIMIR':
            return self.imprimir()
        if tipo == 'LEER':
            return self.leer()
        if tipo == 'SI':
            return self.si()
        if tipo == 'MIENTRAS':
            return self.mientras()
        if tipo == 'SINO':
            self.error("'sino' sin un 'si' antes")
        self.error("Sentencia inválida")

    def declaracion(self):
        linea = self.current_token.linea
        tipo = self.current_token.value          # 'entero', 'decimal', ...
        self.eat(self.current_token.type)
        nombre = self.current_token.value
        self.eat('ID')
        expr = None
        if self.current_token.type == 'ASSIGN':
            self.eat('ASSIGN')
            expr = self.expr()
        self.eat('SEMI')
        return VarDecl(tipo, nombre, expr, linea)

    def asignacion(self):
        linea = self.current_token.linea
        nombre = self.current_token.value
        self.eat('ID')
        self.eat('ASSIGN')
        expr = self.expr()
        self.eat('SEMI')
        return Assign(nombre, expr, linea)

    def imprimir(self):
        linea = self.current_token.linea
        self.eat('IMPRIMIR')
        self.eat('LPAREN')
        expr = self.expr()
        self.eat('RPAREN')
        self.eat('SEMI')
        return Print(expr, linea)

    def leer(self):
        linea = self.current_token.linea
        self.eat('LEER')
        self.eat('LPAREN')
        nombre = self.current_token.value
        self.eat('ID')
        self.eat('RPAREN')
        self.eat('SEMI')
        return Read(nombre, linea)

    def bloque(self):
        self.eat('LBRACE')
        body = []
        while self.current_token.type not in ('RBRACE', 'EOF'):
            body.append(self.statement())
        self.eat('RBRACE')               # si llegó a EOF, aquí da "Se esperaba '}'"
        return body

    def si(self):
        linea = self.current_token.linea
        self.eat('SI')
        self.eat('LPAREN')
        condition = self.expr()
        self.eat('RPAREN')
        body = self.bloque()
        else_body = None
        if self.current_token.type == 'SINO':
            self.eat('SINO')
            if self.current_token.type == 'SI':
                else_body = [self.si()]  # "sino si" = un si dentro del sino
            else:
                else_body = self.bloque()
        return If(condition, body, else_body, linea)

    def mientras(self):
        linea = self.current_token.linea
        self.eat('MIENTRAS')
        self.eat('LPAREN')
        condition = self.expr()
        self.eat('RPAREN')
        body = self.bloque()
        return While(condition, body, linea)

    # ---------------- expresiones ----------------

    def expr(self):
        return self.o_logico()

    def o_logico(self):
        node = self.y_logico()
        while self.current_token.type == 'O':
            tok = self.current_token
            self.eat('O')
            node = BinOp(node, 'o', self.y_logico(), tok.linea)
        return node

    def y_logico(self):
        node = self.comparacion()
        while self.current_token.type == 'Y':
            tok = self.current_token
            self.eat('Y')
            node = BinOp(node, 'y', self.comparacion(), tok.linea)
        return node

    def comparacion(self):
        node = self.suma()
        if self.current_token.type == 'RELOP':
            tok = self.current_token
            self.eat('RELOP')
            node = BinOp(node, tok.value, self.suma(), tok.linea)
        return node

    def suma(self):
        node = self.termino()
        while self.current_token.type in ('PLUS', 'MINUS'):
            tok = self.current_token
            self.eat(tok.type)
            node = BinOp(node, tok.value, self.termino(), tok.linea)
        return node

    def termino(self):
        node = self.unario()
        while self.current_token.type in ('MUL', 'DIV'):
            tok = self.current_token
            self.eat(tok.type)
            node = BinOp(node, tok.value, self.unario(), tok.linea)
        return node

    def unario(self):
        tok = self.current_token
        if tok.type == 'MINUS':
            self.eat('MINUS')
            return UnaryOp('-', self.unario(), tok.linea)
        if tok.type == 'NO':
            self.eat('NO')
            return UnaryOp('no', self.unario(), tok.linea)
        return self.factor()

    def factor(self):
        tok = self.current_token
        if tok.type in ('INT', 'FLOAT'):
            self.eat(tok.type)
            return Num(tok)
        if tok.type == 'STRING':
            self.eat('STRING')
            return Str(tok)
        if tok.type == 'BOOL':
            self.eat('BOOL')
            return Bool(tok)
        if tok.type == 'ID':
            self.eat('ID')
            return Var(tok)
        if tok.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.expr()
            self.eat('RPAREN')
            return node
        self.error("Se esperaba un valor (número, cadena, variable o '(')")