# main.py
# Une las 5 fases del compilador:
#   Fase 1 Lexer -> Fase 2 Parser (AST) -> Fase 3 Semántica -> Fase 4 TAC -> Fase 5 VM
#
# Uso:
#   py main.py tests/valido.txt
#   py main.py tests/valido.txt --solo-lexer       (se detiene tras la Fase 1)
#   py main.py tests/valido.txt --solo-parser      (tras la Fase 2)
#   py main.py tests/valido.txt --solo-semantica   (tras la Fase 3)
#   py main.py tests/valido.txt --solo-tac         (tras la Fase 4)
#   py main.py tests/ciclo_infinito.txt --limite-pasos 50

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lexer.lexer import Lexer
from parser.parser import Parser
from semantic.analizador import AnalizadorSemantico
from intermediate.tac import GeneradorTAC, imprimir_tac
from vm.maquina_virtual import MaquinaVirtual


def titulo(texto):
    print("\n" + "=" * 54)
    print(f"{texto:^54}")
    print("=" * 54)


def main():
    args = sys.argv[1:]
    if not args:
        print("Uso: py main.py <archivo> [--solo-lexer | --solo-parser | "
              "--solo-semantica | --solo-tac] [--limite-pasos N]")
        return

    archivo = args[0]
    limite = 10000
    if '--limite-pasos' in args:
        limite = int(args[args.index('--limite-pasos') + 1])

    if not os.path.exists(archivo):
        print(f"[ERROR]: El archivo '{archivo}' no existe.")
        return
    with open(archivo, 'r', encoding='utf-8') as f:
        codigo = f.read()

    print(f"\n--- Analizando archivo: {archivo} ---")

    try:
        # FASE 1: Lexer
        if '--solo-lexer' in args:
            titulo("FASE 1: TOKENS")
            for tok in Lexer(codigo).tokenizar():
                print(f"  Línea {tok.linea:<3} {tok.type:<10} {tok.value!r}")
            return

        # FASE 2: Parser y AST
        ast = Parser(Lexer(codigo)).parse()
        print("\n[ÉXITO] Fase 2: análisis sintáctico correcto")
        print(f"AST: {ast}")
        if '--solo-parser' in args:
            return

        # FASE 3: Semántica
        analizador = AnalizadorSemantico()
        analizador.visitar(ast)
        print("\n[ÉXITO] Fase 3: análisis semántico correcto")
        titulo("TABLA DE SÍMBOLOS")
        print(f"{'Variable':<20} | {'Tipo':<20}")
        print("-" * 54)
        for nombre, tipo in analizador.tabla_simbolos.items():
            print(f"{nombre:<20} | {tipo:<20}")
        if '--solo-semantica' in args:
            return

        # FASE 4: Código intermedio
        tac = GeneradorTAC().generar(ast)
        titulo("FASE 4: CÓDIGO INTERMEDIO (TAC)")
        imprimir_tac(tac)
        if '--solo-tac' in args:
            return

        # FASE 5: Máquina virtual
        titulo("FASE 5: SALIDA DE LA MÁQUINA VIRTUAL")
        MaquinaVirtual(tac).ejecutar(max_pasos=limite)
        print("\n[ÉXITO] Programa ejecutado correctamente")

    except Exception as e:
        print(f"\n[ERROR]: {e}\n")


if __name__ == '__main__':
    main()