# Compilador LexerParser: Análisis Léxico, Sintáctico y Semántico

**Proyecto incremental de un compilador en Python.** Cada fase se construye sobre la anterior, integrando un soporte de nomenclatura bilingüe, un Árbol de Sintaxis Abstracta (AST), un Analizador Semántico robusto y un reporte formal de la Tabla de Símbolos.

---

Estructura del Proyecto

```text
LexerParser/
├── lexer/
│   └── lexer.py             # Fase 1: Análisis léxico y generación de tokens
├── parser/
│   └── parser.py            # Fase 2: Análisis sintáctico y construcción del AST
├── semantic/
│   └── analizador.py        # Fase 3: Análisis semántico, control de tipos y alcance
├── tests/
│   └── valido.txt           # Casos de prueba institucionales y de validación
├── ast_nodes.py             # Definición de nodos del AST (con soporte bilingüe)
├── main.py                  # Interfaz central de coordinación (Fase 1 → Fase 2 → Fase 3)
└── README.md                # Documentación oficial del repositorio
⚙️ Instrucciones de Ejecución
El compilador está desarrollado en Python 3.10+ sin dependencias externas obligatorias. Desde la raíz del proyecto, puedes ejecutar los análisis de la siguiente manera:

Bash
# Ejecución del flujo completo (Lexer → Parser → Semántico → Tabla de Símbolos)
python main.py tests/valido.txt
🛠️ Arquitectura y Componentes Clave
El compilador procesa el código fuente a través de tres etapas secuenciales estrictas:

Fase 1 (Léxico): Transforma el código fuente plano en un flujo estructurado de tokens válidos, filtrando espacios en blanco y comentarios.

Fase 2 (Sintáctico): Emplea un parser descendente recursivo para validar la gramática y construir el Árbol de Sintaxis Abstracta (AST). Implementa un mapeo de nodos bilingüe (inglés/español) para garantizar flexibilidad institucional (ej. Assign/Asignacion, If/Si, While/Mientras).

Fase 3 (Semántico): Recorre el AST aplicando el Patrón Visitor. Se encarga de verificar la coherencia contextual del programa.

🔍 Reglas Semánticas y Validación
El módulo AnalizadorSemantico implementa las siguientes restricciones de diseño:

Inferencia y Declaración: Las variables se registran automáticamente en la tabla de símbolos durante las asignaciones, infiriendo su tipo de dato (entero, decimal, booleano, cadena).

Uso antes de Declaración: Se valida estrictamente que ninguna variable sea utilizada u operada sin haber sido declarada previamente (lanzando error semántico de tipo NameError o similar).

Control de Tipos:

Las operaciones aritméticas y relacionales validan la compatibilidad de tipos entre operandos.

Las condiciones de las estructuras de control (Si / Mientras) exigen de forma obligatoria una evaluación de tipo booleano.

Formato de la Tabla de Símbolos
Al finalizar exitosamente el análisis semántico, el compilador genera un reporte formal estructurado de las variables y sus respectivos tipos de datos:

Plaintext
Tabla de símbolos: {'edad': 'entero', 'activo': 'booleano'}

  +--------+-----------+----------+
  | Nombre | Categoria | Tipo     |
  +--------+-----------+----------+
  | edad   | variable  | entero   |
  | activo | variable  | booleano |
  +--------+-----------+----------+
Alcance del Proyecto 
El sistema comprueba con rigor la estructura, el alcance y la coherencia de tipos en las declaraciones y expresiones del lenguaje fuente, garantizando una base sólida y escalable para futuras fases de generación de código intermedio u objeto.
