# main.py
import sys
import os
from lexer.lexer import Lexer
from parser.parser import Parser

def main():
    if len(sys.argv) < 2:
        print("Uso: python main.py <archivo_fuente>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        print(f"Error: El archivo '{filepath}' no existe.")
        sys.exit(1)

    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()

    print(f"--- Analizando archivo: {filepath} ---")

    try:
        lexer = Lexer(code)
        parser = Parser(lexer)
        ast = parser.parse()

        print("\n[ÉXITO] ¡Análisis sintáctico exitoso!")
        print("--- AST Generado ---")
        print(ast)

    except Exception as e:
        print(f"\n[ERROR SINTÁCTICO]: {e}")

if __name__ == '__main__':
    main()