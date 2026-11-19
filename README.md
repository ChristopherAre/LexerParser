# LexerParser — Compilador completo en Python

**Curso:** Compiladores — Universidad San Pablo de Guatemala
**Catedrático:** Ing. Carlos Isaac Arenas Guzmán
**Estudiante:** [NOMBRE COMPLETO] — Carné No. [CARNÉ]

Compilador para un lenguaje en español, construido por entregas. El programa fuente pasa por **cinco fases** hasta ejecutarse en una máquina virtual:

```text
código fuente (.txt)
  → FASE 1  Lexer            lexer/lexer.py               → tokens
  → FASE 2  Parser + AST     parser/parser.py             → árbol (ast_nodes.py)
  → FASE 3  Semántica        semantic/analizador.py       → tabla de símbolos y tipos
  → FASE 4  Código TAC       intermediate/tac.py          → instrucciones de tres direcciones
  → FASE 5  Máquina virtual  vm/maquina_virtual.py        → ejecución y salidas
```

---

## Cómo ejecutar

Python 3.10 o superior, solo biblioteca estándar (no requiere `pip install`). Desde la raíz del proyecto:

```bash
py main.py tests/valido.txt                     # las 5 fases, hasta la ejecución
py main.py tests/extension.txt                  # mi extensión personal
py main.py tests/ciclo_mientras.txt
py main.py tests/leer.txt                       # pide un dato por teclado
py main.py tests/ciclo_infinito.txt --limite-pasos 50

py main.py tests/valido.txt --solo-lexer        # se detiene tras la Fase 1
py main.py tests/valido.txt --solo-parser       # tras la Fase 2
py main.py tests/valido.txt --solo-semantica    # tras la Fase 3
py main.py tests/valido.txt --solo-tac          # tras la Fase 4

py -m unittest discover -s tests -v             # 36 pruebas automáticas
```

## Estructura

```text
LexerParser/
├── main.py                  Une las 5 fases (y las opciones --solo-*)
├── ast_nodes.py             Nodos del AST
├── lexer/lexer.py           Fase 1
├── parser/parser.py         Fase 2
├── semantic/analizador.py   Fase 3
├── intermediate/tac.py      Fase 4  ← entrega final
├── vm/maquina_virtual.py    Fase 5  ← entrega final
├── tests/                   Programas .txt y test_compilador.py
└── evidencias/              Salidas de las ejecuciones (.txt y capturas)
```

---

## El lenguaje

```text
entero x = 10;                 // declaración (también: decimal, cadena, booleano)
entero z;                      // sin valor inicial → 0
x = x + 1;                     // asignación
imprimir(x);                   // salida
leer(x);                       // entrada por teclado
si (x > 5) { ... } sino si (x == 5) { ... } sino { ... }
mientras (x > 0) { ... }
/* comentario de bloque */
```

Precedencia de operadores (de mayor a menor): `-` `no` (unarios) → `*` `/` → `+` `-` → `<` `>` `<=` `>=` `==` `!=` → `y` → `o`.

## Fases 1 a 3 (entregas anteriores)

- **Lexer:** reconoce palabras reservadas en español, números enteros y decimales, cadenas, operadores (`<=`, `>=`, `!=`…) y comentarios `//` y `/* */`. Cada token guarda su **línea** para reportar errores.
- **Parser:** descendente recursivo; un método por regla de la gramática (`declaracion`, `si`, `mientras`, `suma`, `termino`…). Construye el AST con nodos `VarDecl`, `Assign`, `Print`, `Read`, `If`, `While`, `BinOp`, `UnaryOp`, `Num`, `Str`, `Bool`, `Var`.
- **Semántica:** patrón Visitor (`visitar_<Nodo>`). Verifica variables no declaradas o duplicadas, compatibilidad de tipos (un `entero` cabe en un `decimal`, al revés no), operadores lógicos solo con booleanos y condiciones de `si`/`mientras` booleanas.

---

## Fase 4: código intermedio (TAC)

Cada instrucción es una tupla `(op, arg1, arg2, res)`. Los temporales son `@t1, @t2…` y las etiquetas `@L1, @L2…`; empiezan con `@` para no chocar con variables del programa (lo comprueba `test_temporal_no_choca_con_variable_t1`).

| Método | Qué genera |
|---|---|
| `generar_Assign()` / `generar_VarDecl()` | Calcula la expresión y emite `ASSIGN fuente → variable`. |
| `generar_Print()` | Calcula la expresión y emite `PRINT`. |
| `generar_If()` | Condición → `JMP_FALSE` → bloque → `LABEL`. Con `sino`, además `JMP` al final y una segunda etiqueta. |
| `generar_While()` | `LABEL inicio` → condición → `JMP_FALSE fin` → bloque → `JMP inicio` → `LABEL fin`. La condición queda **dentro** del ciclo para recalcularse en cada vuelta. |
| `evaluar_expr()` | Literal → el literal; variable → su nombre; operación → primero sus partes (recursión) y luego un temporal nuevo. Por eso en `x + b * 2` el `*` sale antes que el `+`. |

**Ejemplo** (`tests/ciclo_mientras.txt`):

```text
entero x = 0;                000 | ASSIGN     | 0     |      | x
mientras (x < 3) {           001 | LABEL      |       |      | @L1
    imprimir(x);             002 | <          | x     | 3    | @t1
    x = x + 1;               003 | JMP_FALSE  | @t1   |      | @L2
}                            004 | PRINT      | x     |      |
imprimir(x);                 005 | +          | x     | 1    | @t2
                             006 | ASSIGN     | @t2   |      | x
                             007 | JMP        |       |      | @L1
                             008 | LABEL      |       |      | @L2
                             009 | PRINT      | x     |      |

Salida de la VM: 0, 1, 2, 3
```

## Fase 5: máquina virtual

Funciona como un procesador:

- `self.tac`: la lista de instrucciones; `self.ip`: cuál toca ejecutar.
- `self.memoria`: el valor de cada variable y temporal.
- `self.etiquetas`: en qué posición está cada `LABEL`, para los saltos.
- Ciclo: leer la instrucción en `ip` → ejecutarla → avanzar, o saltar con `JMP` / `JMP_FALSE`.

Métodos principales: `instruccion_operacion`, `instruccion_imprimir`, `instruccion_salto` e `instruccion_salto_condicional`. Las comparaciones dan `1` (verdadero) o `0` (falso).

**Errores que solo aparecen al ejecutar:** división entre cero, **límite de pasos** (detiene un `mientras` infinito) y `leer` con un dato que no es del tipo de la variable.

---

## Extensión personal en TAC y VM

La decisión de qué cambiar depende del **nodo AST**, no solo del token:

| Extensión | Nodo AST | ¿Cambia el TAC? | ¿Cambia la VM? | Cómo funciona |
|---|---|---|---|---|
| `decimal` | `Num` (valor float) | Sí: literal `'3.14'` | Sí | `/` es división **entera** entre dos enteros (`7 / 2 = 3`) y **normal** si hay un decimal (`7.0 / 2 = 3.5`). |
| `cadena` | `Str` | Sí: literal `'"hola"'` | Sí | Literal entre comillas; `+` une dos cadenas. |
| `booleano` | `Bool` | Sí: `'1'` / `'0'` | No | Igual que las comparaciones. |
| `<=` `>=` `!=` | `BinOp` | No (el genérico ya los emite) | Sí | Agregados a `OPERADORES`. |
| `y`, `o` | `BinOp` | No | Sí | Evaluación **directa**, sin cortocircuito: los dos lados ya se calcularon antes. |
| `no`, `-` unario | `UnaryOp` | Sí: `NO`, `NEG` | Sí | Instrucciones de un solo operando. |
| `sino`, `sino si` | `If.else_body` | Sí | No | Usa `JMP`, `JMP_FALSE` y `LABEL` que ya existían. |
| `leer` | `Read` | Sí: `READ tipo → var` | Sí | La VM pide el dato por teclado y lo convierte al tipo de la variable. |
| `//`, `/* */` | — | No | No | El lexer los descarta: nunca llegan al AST. |

**Programa de la extensión** (`tests/extension.txt`) y su TAC:

```text
decimal precio = 3.14;              000 | ASSIGN     | 3.14    |       | precio
cadena saludo = "hola";             001 | ASSIGN     | "hola"  |       | saludo
booleano activo = verdadero;        002 | ASSIGN     | 1       |       | activo
entero a = 5;                       003 | ASSIGN     | 5       |       | a
si (a < 1 + 2) {                    004 | +          | 1       | 2     | @t1
    imprimir("chico");              005 | <          | a       | @t1   | @t2
} sino si (a >= 5 y no falso) {     006 | JMP_FALSE  | @t2     |       | @L1
    imprimir(saludo);               007 | PRINT      | "chico" |       |
} sino {                            008 | JMP        |         |       | @L2
    imprimir(-a);                   009 | LABEL      |         |       | @L1
}                                   010 | >=         | a       | 5     | @t3
                                    011 | NO         | 0       |       | @t4
                                    012 | y          | @t3     | @t4   | @t5
                                    013 | JMP_FALSE  | @t5     |       | @L3
                                    014 | PRINT      | saludo  |       |
                                    015 | JMP        |         |       | @L4
                                    016 | LABEL      |         |       | @L3
                                    017 | NEG        | a       |       | @t6
                                    018 | PRINT      | @t6     |       |
                                    019 | LABEL      |         |       | @L4
                                    020 | LABEL      |         |       | @L2

Salida de la VM: hola
```

**Archivos que cambié para la extensión:** `lexer/lexer.py` (tokens), `parser/parser.py` y `ast_nodes.py` (nodos `Str`, `Bool`, `UnaryOp`, `Read`, `sino`), `semantic/analizador.py` (reglas de tipos), `intermediate/tac.py` (`NEG`, `NO`, `READ`, literales) y `vm/maquina_virtual.py` (decimales, cadenas, `y`/`o`, `NEG`/`NO`, `READ`).

---

## Pruebas y evidencias

| Archivo de prueba | Resultado esperado | Evidencia |
|---|---|---|
| `tests/valido.txt` | Imprime `50` | `evidencias/01_programa_valido.txt` |
| `tests/ciclo_mientras.txt` | Imprime `0 1 2 3` | `evidencias/02_ciclo_mientras.txt` |
| `tests/extension.txt` | Imprime `hola` | `evidencias/03_extension.txt` |
| `tests/error_sintactico.txt` | Error sintáctico, línea 2 | `evidencias/04_error_sintactico.txt` |
| `tests/error_duplicada.txt` | Variable ya declarada, línea 2 | `evidencias/05_error_semantico_duplicada.txt` |
| `tests/error_tipo.txt` | Tipos incompatibles, línea 2 | `evidencias/06_error_semantico_tipo.txt` |
| `tests/error_condicion.txt` | Condición no booleana, línea 2 | `evidencias/07_error_condicion.txt` |
| `tests/division_cero.txt` | Error de ejecución: división entre cero | `evidencias/08_error_division_cero.txt` |
| `tests/ciclo_infinito.txt --limite-pasos 50` | Error de ejecución: límite de pasos | `evidencias/09_error_ciclo_infinito.txt` |
| `tests/leer.txt` (entrada `20`) | Imprime `mayor de edad` | `evidencias/10_leer.txt` |
| `py -m unittest discover -s tests -v` | `Ran 36 tests … OK` | `evidencias/11_pruebas_unitarias.txt` |
