# lexer/lexer.py
# FASE 1: Analizador léxico. Convierte el código fuente en tokens.


class Token:
    def __init__(self, type_, value, linea=1):
        self.type = type_
        self.value = value
        self.linea = linea          # NUEVO: línea donde apareció el token

    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, linea={self.linea})"


# Palabras reservadas del lenguaje (en español)
PALABRAS_RESERVADAS = {
    'entero':    'ENTERO',
    'decimal':   'DECIMAL',
    'cadena':    'CADENA',
    'booleano':  'BOOLEANO',
    'si':        'SI',
    'sino':      'SINO',
    'mientras':  'MIENTRAS',
    'imprimir':  'IMPRIMIR',
    'leer':      'LEER',
    'verdadero': 'BOOL',
    'falso':     'BOOL',
    'y':         'Y',
    'o':         'O',
    'no':        'NO',
}


class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.linea = 1              # NUEVO: contador de líneas
        self.current_char = self.text[self.pos] if self.text else None

    def error(self):
        raise Exception(
            f"Error léxico (Línea {self.linea}): Carácter inválido '{self.current_char}'"
        )

    def advance(self):
        if self.current_char == '\n':
            self.linea += 1         # cada salto de línea suma una línea
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def peek(self):
        """Mira el siguiente carácter sin avanzar."""
        sig = self.pos + 1
        return self.text[sig] if sig < len(self.text) else None

    def token(self, tipo, valor):
        return Token(tipo, valor, self.linea)

    def skip_whitespace(self):
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def skip_comentario_linea(self):
        while self.current_char is not None and self.current_char != '\n':
            self.advance()

    def skip_comentario_bloque(self):
        linea_inicio = self.linea
        self.advance()  # '/'
        self.advance()  # '*'
        while self.current_char is not None:
            if self.current_char == '*' and self.peek() == '/':
                self.advance()
                self.advance()
                return
            self.advance()
        raise Exception(f"Error léxico (Línea {linea_inicio}): comentario /* sin cerrar")

    def number(self):
        linea = self.linea
        result = ''
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        # Solo es decimal si después del punto viene un dígito (3.14)
        if self.current_char == '.' and self.peek() is not None and self.peek().isdigit():
            result += '.'
            self.advance()
            while self.current_char is not None and self.current_char.isdigit():
                result += self.current_char
                self.advance()
            return Token('FLOAT', float(result), linea)
        return Token('INT', int(result), linea)

    def string(self):
        linea = self.linea
        self.advance()  # comilla de apertura
        result = ''
        while self.current_char is not None and self.current_char != '"':
            if self.current_char == '\n':
                raise Exception(f"Error léxico (Línea {linea}): cadena sin cerrar")
            result += self.current_char
            self.advance()
        if self.current_char is None:
            raise Exception(f"Error léxico (Línea {linea}): cadena sin cerrar")
        self.advance()  # comilla de cierre
        return Token('STRING', result, linea)

    def _id(self):
        linea = self.linea
        result = ''
        while self.current_char is not None and (self.current_char.isalnum() or self.current_char == '_'):
            result += self.current_char
            self.advance()
        tipo = PALABRAS_RESERVADAS.get(result, 'ID')
        return Token(tipo, result, linea)

    def get_next_token(self):
        while self.current_char is not None:
            c = self.current_char

            if c.isspace():
                self.skip_whitespace()
                continue

            # Comentarios: // y /* */
            if c == '/' and self.peek() == '/':
                self.skip_comentario_linea()
                continue
            if c == '/' and self.peek() == '*':
                self.skip_comentario_bloque()
                continue

            if c.isalpha() or c == '_':
                return self._id()
            if c.isdigit():
                return self.number()
            if c == '"':
                return self.string()

            # Operadores de dos caracteres: ==  !=  <=  >=
            dos = c + (self.peek() or '')
            if dos in ('==', '!=', '<=', '>='):
                tok = self.token('RELOP', dos)
                self.advance()
                self.advance()
                return tok

            simples = {
                '=': 'ASSIGN', '<': 'RELOP', '>': 'RELOP',
                '+': 'PLUS', '-': 'MINUS', '*': 'MUL', '/': 'DIV',
                ';': 'SEMI', ',': 'COMMA',
                '{': 'LBRACE', '}': 'RBRACE',
                '(': 'LPAREN', ')': 'RPAREN',
            }
            if c in simples:
                tok = self.token(simples[c], c)
                self.advance()
                return tok

            self.error()

        return Token('EOF', None, self.linea)

    def tokenizar(self):
        """Devuelve la lista completa de tokens (útil para --solo-lexer y pruebas)."""
        tokens = []
        while True:
            tok = self.get_next_token()
            tokens.append(tok)
            if tok.type == 'EOF':
                return tokens