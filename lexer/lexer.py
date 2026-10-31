# lexer/lexer.py

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)})"

class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None

    def error(self):
        raise Exception(f"Error léxico: Carácter inválido '{self.current_char}'")

    def advance(self):
        self.pos += 1
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def number(self):
        result = ''
        while self.current_char is not None and (self.current_char.isdigit() or self.current_char == '.'):
            result += self.current_char
            self.advance()
        if '.' in result:
            return Token('FLOAT', float(result))
        else:
            return Token('INT', int(result))

    def _id(self):
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        
        # Palabras reservadas
        keywords = {'if': 'IF', 'else': 'ELSE', 'while': 'WHILE'}
        return Token(keywords.get(result, 'ID'), result)

    def get_next_token(self):
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            # Comentarios de una línea estilo //
            if self.current_char == '/' and self.pos + 1 < len(self.text) and self.text[self.pos + 1] == '/':
                while self.current_char is not None and self.current_char != '\n':
                    self.advance()
                continue

            if self.current_char.isalpha() or self.current_char == '_':
                return self._id()

            if self.current_char.isdigit():
                return self.number()

            if self.current_char == '=':
                self.advance()
                if self.current_char == '=':
                    self.advance()
                    return Token('EQ', '==')
                return Token('ASSIGN', '=')

            if self.current_char == '<':
                self.advance()
                return Token('LT', '<')

            if self.current_char == '>':
                self.advance()
                return Token('GT', '>')

            if self.current_char == '+':
                self.advance()
                return Token('PLUS', '+')

            if self.current_char == '-':
                self.advance()
                return Token('MINUS', '-')

            if self.current_char == '*':
                self.advance()
                return Token('MUL', '*')

            if self.current_char == '/':
                self.advance()
                return Token('DIV', '/')

            if self.current_char == ';':
                self.advance()
                return Token('SEMI', ';')

            if self.current_char == '{':
                self.advance()
                return Token('LBRACE', '{')

            if self.current_char == '}':
                self.advance()
                return Token('RBRACE', '}')

            if self.current_char == '(':
                self.advance()
                return Token('LPAREN', '(')

            if self.current_char == ')':
                self.advance()
                return Token('RPAREN', ')')

            self.error()

        return Token('EOF', None)