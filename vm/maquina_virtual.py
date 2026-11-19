# vm/maquina_virtual.py
# FASE 5: Máquina virtual. EJECUTA el TAC instrucción por instrucción.
#
# Funciona como un procesador:
#   self.tac        la lista de instrucciones (el "programa")
#   self.ip         número de la instrucción que toca ejecutar
#   self.memoria    valor de cada variable y temporal
#   self.etiquetas  posición de cada LABEL, para poder saltar
#
# Ciclo de ejecutar():  leer instrucción -> ejecutarla -> avanzar (o saltar)
#
# Valores: entero (int), decimal (float), cadena (str), booleano como 1 / 0.
#
# Errores que solo se detectan AL EJECUTAR:
#   - división entre cero
#   - límite de pasos (detiene un 'mientras' infinito)
#   - 'leer' recibe un dato que no es del tipo de la variable

OPERADORES = {'+', '-', '*', '/', '<', '>', '<=', '>=', '==', '!=', 'y', 'o'}


class ErrorEjecucion(Exception):
    pass


class MaquinaVirtual:
    def __init__(self, tac, entrada=None):
        self.tac = list(tac)
        self.ip = 0
        self.memoria = {}
        self.salidas = []
        self.entrada = entrada or input     # las pruebas pueden pasar respuestas fijas
        # Se registran las etiquetas antes de ejecutar, para poder saltar hacia adelante
        self.etiquetas = {res: i for i, (op, _, _, res) in enumerate(self.tac) if op == 'LABEL'}

    # ---------------- valores ----------------

    def obtener_val(self, arg):
        """Convierte un argumento del TAC en su valor real."""
        if arg is None:
            return None
        if arg.startswith('"') and arg.endswith('"'):
            return arg[1:-1]                        # cadena literal
        try:
            return int(arg)                         # entero literal
        except ValueError:
            pass
        try:
            return float(arg)                       # decimal literal
        except ValueError:
            pass
        if arg not in self.memoria:
            raise ErrorEjecucion(f"Error de ejecución: '{arg}' no tiene valor")
        return self.memoria[arg]                    # variable o temporal

    def guardar(self, destino, valor):
        self.memoria[destino] = valor

    # ---------------- ciclo principal ----------------

    def ejecutar(self, max_pasos=10000):
        pasos = 0
        while self.ip < len(self.tac):
            pasos += 1
            if pasos > max_pasos:
                raise ErrorEjecucion(
                    f"Error de ejecución: se superó el límite de {max_pasos} pasos "
                    f"(posible ciclo infinito)")

            op, a1, a2, res = self.tac[self.ip]
            self.ip += 1                            # por defecto, la siguiente

            if op == 'ASSIGN':
                self.guardar(res, self.obtener_val(a1))
            elif op in OPERADORES:
                self.instruccion_operacion(op, a1, a2, res)
            elif op in ('NEG', 'NO'):
                self.instruccion_unaria(op, a1, res)
            elif op == 'PRINT':
                self.instruccion_imprimir(a1)
            elif op == 'READ':
                self.instruccion_leer(a1, res)
            elif op == 'JMP':
                self.instruccion_salto(res)
            elif op == 'JMP_FALSE':
                self.instruccion_salto_condicional(a1, res)
            elif op == 'LABEL':
                pass                                # solo marca una posición
            else:
                raise ErrorEjecucion(f"Error de ejecución: instrucción desconocida '{op}'")
        return self.salidas

    # ---------------- instrucciones ----------------

    def instruccion_operacion(self, op, a1, a2, res):
        a = self.obtener_val(a1)
        b = self.obtener_val(a2)
        if op == '+':
            valor = a + b                           # suma o une cadenas
        elif op == '-':
            valor = a - b
        elif op == '*':
            valor = a * b
        elif op == '/':
            if b == 0:
                raise ErrorEjecucion("Error de ejecución: división entre cero")
            if isinstance(a, int) and isinstance(b, int):
                valor = int(a / b)                  # entero / entero = división entera (7/2 = 3)
            else:
                valor = a / b                       # con un decimal: división normal
        elif op == '<':
            valor = 1 if a < b else 0
        elif op == '>':
            valor = 1 if a > b else 0
        elif op == '<=':
            valor = 1 if a <= b else 0
        elif op == '>=':
            valor = 1 if a >= b else 0
        elif op == '==':
            valor = 1 if a == b else 0
        elif op == '!=':
            valor = 1 if a != b else 0
        elif op == 'y':
            valor = 1 if (a and b) else 0
        elif op == 'o':
            valor = 1 if (a or b) else 0
        self.guardar(res, valor)

    def instruccion_unaria(self, op, a1, res):
        a = self.obtener_val(a1)
        self.guardar(res, -a if op == 'NEG' else (0 if a else 1))

    def instruccion_imprimir(self, a1):
        valor = self.obtener_val(a1)
        self.salidas.append(valor)
        print(valor)

    def instruccion_salto(self, etiqueta):
        if etiqueta not in self.etiquetas:
            raise ErrorEjecucion(f"Error de ejecución: etiqueta '{etiqueta}' no existe")
        self.ip = self.etiquetas[etiqueta]

    def instruccion_salto_condicional(self, condicion, etiqueta):
        if not self.obtener_val(condicion):         # 0 = falso -> saltar
            self.instruccion_salto(etiqueta)

    def instruccion_leer(self, tipo, destino):
        texto = self.entrada(f"Ingrese un valor ({tipo}) para '{destino}': ").strip()
        try:
            if tipo == 'entero':
                valor = int(texto)
            elif tipo == 'decimal':
                valor = float(texto)
            elif tipo == 'booleano':
                if texto not in ('verdadero', 'falso'):
                    raise ValueError
                valor = 1 if texto == 'verdadero' else 0
            else:
                valor = texto                       # cadena
        except ValueError:
            raise ErrorEjecucion(
                f"Error de ejecución: '{texto}' no es un valor válido de tipo {tipo}")
        self.guardar(destino, valor)