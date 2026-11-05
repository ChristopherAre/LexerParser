import sys
import os

# Asegurar que el directorio actual esté en el path para importar módulos locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Intentar importar el Lexer y el Parser desde sus respectivas carpetas/módulos
try:
    from lexer.lexer import Lexer
except ImportError:
    try:
        from lexer import Lexer
    except ImportError:
        Lexer = None

try:
    from parser.parser import Parser
except ImportError:
    try:
        from parser import Parser
    except ImportError:
        Parser = None

from semantic.analizador import AnalizadorSemantico

def main():
    # Validar que se haya pasado el archivo de prueba como argumento
    if len(sys.argv) < 2:
        print("Uso correcto: py main.py <ruta_archivo>")
        print("Ejemplo: py main.py tests/valido.txt")
        return

    archivo_path = sys.argv[1]
    print(f"\n--- Analizando archivo: {archivo_path} ---")

    if not os.path.exists(archivo_path):
        print(f"\n[ERROR]: El archivo '{archivo_path}' no existe o la ruta es incorrecta.")
        return

    # Leer el contenido del archivo de código fuente
    try:
        with open(archivo_path, 'r', encoding='utf-8') as f:
            codigo = f.read()
    except Exception as e:
        print(f"\n[ERROR]: No se pudo leer el archivo. Detalle: {e}")
        return

    try:
        # 1. Fase de Análisis Léxico y Sintáctico (Generación del AST)
        if Parser is not None and Lexer is not None:
            # Inicializar el Lexer pasando el código fuente directamente
            lexer_instancia = Lexer(codigo)
            parser_instancia = Parser(lexer_instancia)
            
            # Intentar diferentes nombres de métodos comunes para iniciar el parsing
            if hasattr(parser_instancia, 'parse'):
                # Algunos parsers toman el código en .parse(), otros usan el lexer interno
                try:
                    ast = parser_instancia.parse(codigo)
                except TypeError:
                    ast = parser_instancia.parse()
            elif hasattr(parser_instancia, 'compilar'):
                ast = parser_instancia.compilar(codigo)
            else:
                ast = parser_instancia()
        else:
            raise ImportError("No se pudo importar la clase Parser o Lexer. Verifica las rutas de tus carpetas.")

        print("\n[ÉXITO] ¡Análisis sintáctico exitoso!")
        print(f"--- AST Generado ---\n{ast}\n")

        # 2. Fase de Análisis Semántico
        analizador = AnalizadorSemantico()
        analizador.visitar(ast)

        print("[ÉXITO] ¡Análisis semántico exitoso!")

        # 3. Reporte Formal de la Tabla de Símbolos (Requerido por la cátedra)
        print("\n" + "="*45)
        print(f"{'TABLA DE SÍMBOLOS':^45}")
        print("="*45)
        print(f"{'Variable':<20} | {'Tipo':<20}")
        print("-" * 45)
        
        if hasattr(analizador, 'tabla_simbolos') and analizador.tabla_simbolos:
            for nombre, tipo in analizador.tabla_simbolos.items():
                print(f"{nombre:<20} | {tipo:<20}")
        else:
            print(f"{'No se registraron variables':<45}")
        print("="*45 + "\n")

    except Exception as e:
        print(f"\n[ERROR]: {e}\n")

if __name__ == '__main__':
    main()