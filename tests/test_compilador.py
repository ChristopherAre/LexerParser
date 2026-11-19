# tests/test_compilador.py
# Pruebas automáticas de las 5 fases del compilador.
# Ejecutar desde la raíz del proyecto:
#     py -m unittest discover -s tests -v

import os
import sys
import unittest
from contextlib import redirect_stdout
from io import StringIO

# Permite importar los módulos del proyecto (lexer, parser, ...) desde tests/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexer.lexer import Lexer
from parser.parser import Parser
from semantic.analizador import AnalizadorSemantico, ErrorSemantico
from intermediate.tac import GeneradorTAC
from vm.maquina_virtual import MaquinaVirtual, ErrorEjecucion


def tipos_tokens(codigo):
    return [t.type for t in Lexer(codigo).tokenizar()]


def parsear(codigo):
    return Parser(Lexer(codigo)).parse()


def analizar(codigo):
    ast = parsear(codigo)
    sem = AnalizadorSemantico()
    sem.visitar(ast)
    return ast, sem.tabla_simbolos


def compilar(codigo):
    ast, _ = analizar(codigo)
    return GeneradorTAC().generar(ast)


def correr(codigo, max_pasos=10000, entradas=None):
    tac = compilar(codigo)
    respuestas = iter(entradas or [])
    vm = MaquinaVirtual(tac, entrada=lambda _msg: next(respuestas))
    with redirect_stdout(StringIO()):       # no ensuciar la consola
        return vm.ejecutar(max_pasos=max_pasos)


# ---------------- FASE 1: LEXER ----------------

class TestLexer(unittest.TestCase):
    def test_palabras_reservadas(self):
        self.assertEqual(tipos_tokens('entero si sino mientras imprimir'),
                         ['ENTERO', 'SI', 'SINO', 'MIENTRAS', 'IMPRIMIR', 'EOF'])

    def test_identificador_que_empieza_como_reservada(self):
        # 'nota' empieza con 'no' pero es un ID
        self.assertEqual(tipos_tokens('nota'), ['ID', 'EOF'])

    def test_numeros_y_cadenas(self):
        self.assertEqual(tipos_tokens('10 3.14 "hola"'), ['INT', 'FLOAT', 'STRING', 'EOF'])

    def test_operadores_dobles(self):
        valores = [t.value for t in Lexer('<= >= == != < >').tokenizar()[:-1]]
        self.assertEqual(valores, ['<=', '>=', '==', '!=', '<', '>'])

    def test_comentarios_se_ignoran(self):
        self.assertEqual(tipos_tokens('// linea\n/* bloque\n */ x'), ['ID', 'EOF'])

    def test_cuenta_lineas(self):
        tokens = Lexer('entero a;\n\nentero b;').tokenizar()
        self.assertEqual(tokens[3].linea, 3)

    def test_error_lexico(self):
        with self.assertRaisesRegex(Exception, 'Línea 1'):
            Lexer('x = 5 @;').tokenizar()


# ---------------- FASE 2: PARSER ----------------

class TestParser(unittest.TestCase):
    def test_precedencia_multiplicacion(self):
        ast = parsear('entero x = 1 + 2 * 3;')
        self.assertEqual(repr(ast.statements[0].expr), 'BinOp(Num(1) + BinOp(Num(2) * Num(3)))')

    def test_precedencia_comparacion(self):
        ast = parsear('entero a = 1;\nsi (a < 1 + 2) { a = 0; }')
        self.assertEqual(repr(ast.statements[1].condition), 'BinOp(Var(a) < BinOp(Num(1) + Num(2)))')

    def test_sino_si(self):
        ast = parsear('si (verdadero) { } sino si (falso) { } sino { }')
        self.assertEqual(type(ast.statements[0].else_body[0]).__name__, 'If')

    def test_error_falta_punto_y_coma(self):
        with self.assertRaisesRegex(Exception, "Se esperaba ';'"):
            parsear('entero x = 5\nentero b = 2;')

    def test_error_bloque_sin_cerrar(self):
        with self.assertRaisesRegex(Exception, "Se esperaba '}'"):
            parsear('si (verdadero) { imprimir(1);')

    def test_error_sino_sin_si(self):
        with self.assertRaisesRegex(Exception, "'sino' sin un 'si'"):
            parsear('sino { }')


# ---------------- FASE 3: SEMÁNTICA ----------------

class TestSemantica(unittest.TestCase):
    def test_tabla_de_simbolos(self):
        _, tabla = analizar('entero a = 1;\ndecimal d = 2.5;\ncadena c = "x";\nbooleano b = falso;')
        self.assertEqual(tabla, {'a': 'entero', 'd': 'decimal', 'c': 'cadena', 'b': 'booleano'})

    def test_entero_cabe_en_decimal(self):
        analizar('decimal d = 5;')          # no debe lanzar error

    def test_no_declarada(self):
        with self.assertRaisesRegex(ErrorSemantico, "no declarada|sin previa declaración"):
            analizar('x = 5;')

    def test_duplicada(self):
        with self.assertRaisesRegex(ErrorSemantico, 'ya fue declarada'):
            analizar('entero x = 1;\nentero x = 2;')

    def test_tipo_incompatible(self):
        with self.assertRaisesRegex(ErrorSemantico, 'Línea 2'):
            analizar('entero x = 1;\nx = "hola";')

    def test_decimal_no_cabe_en_entero(self):
        with self.assertRaises(ErrorSemantico):
            analizar('entero x = 2.5;')

    def test_condicion_no_booleana(self):
        with self.assertRaisesRegex(ErrorSemantico, 'booleana'):
            analizar('entero x = 1;\nsi (x) { }')

    def test_logico_con_entero(self):
        with self.assertRaises(ErrorSemantico):
            analizar('booleano b = 1 y verdadero;')


# ---------------- FASE 4: TAC ----------------

class TestTAC(unittest.TestCase):
    def test_asignacion(self):
        self.assertEqual(compilar('entero x = 5;'), [('ASSIGN', '5', None, 'x')])

    def test_orden_de_operaciones(self):
        self.assertEqual(compilar('entero x = 5 + 3 * 2;'), [
            ('*', '3', '2', '@t1'),
            ('+', '5', '@t1', '@t2'),
            ('ASSIGN', '@t2', None, 'x'),
        ])

    def test_mientras_condicion_dentro_del_ciclo(self):
        tac = compilar('entero x = 0;\nmientras (x < 3) { x = x + 1; }')
        ops = [i[0] for i in tac]
        self.assertEqual(ops, ['ASSIGN', 'LABEL', '<', 'JMP_FALSE', '+', 'ASSIGN', 'JMP', 'LABEL'])

    def test_temporal_no_choca_con_variable_t1(self):
        tac = compilar('entero t1 = 1 + 2;')
        self.assertEqual(tac[0][3], '@t1')
        self.assertEqual(tac[1][3], 't1')


# ---------------- FASE 5: MÁQUINA VIRTUAL ----------------

class TestMaquinaVirtual(unittest.TestCase):
    def test_imprimir_expresion(self):
        self.assertEqual(correr('imprimir(5 + 3 * 2);'), [11])

    def test_si_sino(self):
        codigo = 'entero a = 5;\nsi (a > 3) { imprimir("si"); } sino { imprimir("no"); }'
        self.assertEqual(correr(codigo), ['si'])

    def test_sino_si(self):
        codigo = ('entero a = 2;\nsi (a == 1) { imprimir(1); } '
                  'sino si (a == 2) { imprimir(2); } sino { imprimir(3); }')
        self.assertEqual(correr(codigo), [2])

    def test_ciclo_mientras(self):
        codigo = 'entero x = 0;\nmientras (x < 3) { imprimir(x); x = x + 1; }'
        self.assertEqual(correr(codigo), [0, 1, 2])

    def test_division_entera_y_decimal(self):
        self.assertEqual(correr('imprimir(7 / 2);\nimprimir(7.0 / 2);'), [3, 3.5])

    def test_concatenar_cadenas(self):
        self.assertEqual(correr('cadena s = "ho" + "la";\nimprimir(s);'), ['hola'])

    def test_logicos_y_unarios(self):
        self.assertEqual(correr('imprimir(verdadero y no falso);\nimprimir(-5 + 2);'), [1, -3])

    def test_leer(self):
        codigo = 'entero n;\nleer(n);\nimprimir(n * 2);'
        self.assertEqual(correr(codigo, entradas=['21']), [42])

    def test_error_division_cero(self):
        with self.assertRaisesRegex(ErrorEjecucion, 'división entre cero'):
            correr('entero a = 0;\nimprimir(10 / a);')

    def test_error_limite_de_pasos(self):
        with self.assertRaisesRegex(ErrorEjecucion, 'límite'):
            correr('mientras (verdadero) { }', max_pasos=50)

    def test_error_leer_tipo(self):
        with self.assertRaisesRegex(ErrorEjecucion, 'no es un valor válido'):
            correr('entero n;\nleer(n);', entradas=['hola'])


if __name__ == '__main__':
    unittest.main()