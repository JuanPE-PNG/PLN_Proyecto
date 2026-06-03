"""
Escape Room RPG en Español

Motor principal del juego:
input -> tokenizar -> parsear -> DCG/semántica -> ATN -> output
"""

import os

from src.grammar import GRAMATICA, formatear_gramatica
from src.lexer import formatear_tokens, tokenizar
from src.parser import formatear_arboles, parsear
from src.semantica import formatear_acciones, interpretar_todos
from src.atn import ATNJuego


def limpiar_pantalla():
    """
    Limpia la terminal para que el panel de comandos siempre quede visible.
    """
    os.system("cls" if os.name == "nt" else "clear")


def obtener_inventario(juego: ATNJuego) -> str:
    """
    Devuelve el inventario actual del jugador en formato legible.
    """
    if not juego.estado.inventario:
        return "vacío"

    # nombres de los objetos separados por comas
    return ", ".join(juego.estado.inventario.keys())


def mostrar_panel(
    juego: ATNJuego,
    ultima_entrada: str = "",
    ultima_respuesta: str = "",
    cambio: str = "",
):
    """
    Muestra un panel fijo en cada turno.
    Esto evita que el usuario tenga que subir en la terminal para recordar
    los comandos disponibles.
    """

    limpiar_pantalla()

    print("============================================================")
    print("   ESCAPE ROOM RPG — DFA + CFG + Parser Earley + DCG + ATN")
    print("============================================================")
    print()

    print("COMANDOS DISPONIBLES:")
    print("  Movimiento:     ir al norte | ir al sur | ir al este | ir al oeste")
    print("  Objetos:        tomar la llave | dejar la llave | tomar la antorcha")
    print("  Interacción:    abrir la puerta | abrir el cofre | leer el pergamino")
    print("  Exploración:    examinar la pared | examinar el cofre | mirar")
    print("  Sistema:        inventario | estado | ayuda | debug | gramatica | salir")
    print()

    print("ESTADO ACTUAL:")
    print(f"  Sala: {juego.estado.sala_actual}")
    print(f"  Inventario: {obtener_inventario(juego)}")
    print()

    if ultima_entrada:
        print("ÚLTIMA ACCIÓN:")
        print(f"  > {ultima_entrada}")

        if cambio:
            print(f"  Cambio detectado: {cambio}")
        else:
            print("  Cambio detectado: sin cambios importantes en el estado.")

        print()

    if ultima_respuesta:
        print("RESPUESTA:")
        print(ultima_respuesta)
        print()

    print("------------------------------------------------------------")
    print("Escribe tu comando:")


def capturar_estado(juego: ATNJuego) -> dict:
    """
    Captura una fotografía simple del estado actual del juego.
    Sirve para comparar antes y después de ejecutar un comando.
    """
    return {
        "sala": juego.estado.sala_actual,
        "inventario": set(juego.estado.inventario.keys()),
        "banderas": dict(juego.estado.banderas),
        "terminado": juego.estado.terminado,
    }


def detectar_cambio_estado(antes: dict, despues: dict) -> str:
    """
    Compara el estado antes y después de ejecutar una acción.
    Devuelve un mensaje breve indicando qué cambió.
    """
    cambios = []

    if antes["sala"] != despues["sala"]:
        cambios.append(f"cambiaste de sala: {antes['sala']} → {despues['sala']}")

    if antes["inventario"] != despues["inventario"]:
        agregados = despues["inventario"] - antes["inventario"]
        removidos = antes["inventario"] - despues["inventario"]

        if agregados:
            cambios.append("inventario actualizado: +" + ", ".join(agregados))

        if removidos:
            cambios.append("inventario actualizado: -" + ", ".join(removidos))

    # compara las banderas, que indican eventos importantes o condiciones del juego
    for bandera, valor_despues in despues["banderas"].items():
        valor_antes = antes["banderas"].get(bandera)

        if valor_antes != valor_despues:
            cambios.append(f"{bandera}: {valor_antes} → {valor_despues}")

    if antes["terminado"] != despues["terminado"]:
        cambios.append("condición de victoria alcanzada")

    if not cambios:
        return ""

    return "; ".join(cambios)



def procesar_comando(juego: ATNJuego, entrada: str, debug: bool = False) -> tuple[str, str]:
    """
    Procesa una entrada completa del usuario usando todo el pipeline:

    1. Lexer / DFA: convierte texto en tokens.
    2. Parser / CFG: valida la estructura sintáctica.
    3. DCG / unificación: extrae la intención semántica.
    4. ATN: ejecuta la acción sobre el mundo del juego.

    Retorna:
    - respuesta visible para el jugador.
    - descripción del cambio de estado.
    """

    estado_antes = capturar_estado(juego)

    tokens = tokenizar(entrada)
    arboles = parsear(tokens)
    acciones = interpretar_todos(arboles)

    salida: list[str] = []

    if debug:
        salida.append("Tokens:")
        salida.append(formatear_tokens(tokens))

        salida.append("\nÁrbol de derivación:")
        salida.append(formatear_arboles(arboles))

        salida.append("\nIntención:")
        salida.append(formatear_acciones(acciones))

        salida.append("\nATN / Mundo:")

    if not acciones:
        salida.append(
            "No entendí ese comando como una acción válida del juego. "
            "Prueba con algo como 'tomar la llave', 'ir al norte' o 'ayuda'."
        )
        return "\n".join(salida), ""

    # Detección de ambigüedad: el parser pudo devolver varias derivaciones.
    # Nos quedamos con las interpretaciones semánticamente distintas.
    interpretaciones: list = []
    vistas: set[str] = set()
    for a in acciones:
        if repr(a) not in vistas:
            vistas.add(repr(a))
            interpretaciones.append(a)

    if len(interpretaciones) > 1:
        salida.append(
            f"Comando ambiguo: detecté {len(interpretaciones)} interpretaciones posibles:"
        )
        for k, a in enumerate(interpretaciones, 1):
            salida.append(f"  {k}. {a!r}")
        salida.append(f"Tomaré la más natural → {interpretaciones[0]!r}")
        salida.append("")

    # Ejecuta la interpretación preferida (la de adjunción más natural).
    respuesta = juego.ejecutar(interpretaciones[0])
    salida.append(respuesta)

    estado_despues = capturar_estado(juego)
    cambio = detectar_cambio_estado(estado_antes, estado_despues)

    return "\n".join(salida), cambio



def main():
    juego = ATNJuego()
    debug = False

    ultima_entrada = ""
    ultima_respuesta = (
        "Bienvenido. Estás atrapado en una torre antigua. "
        "Explora el lugar, recoge objetos y encuentra la salida."
    )
    ultimo_cambio = ""

    while True:
        mostrar_panel(
            juego,
            ultima_entrada=ultima_entrada,
            ultima_respuesta=ultima_respuesta,
            cambio=ultimo_cambio,
        )

        try:
            entrada = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nHasta luego.")
            break

        if not entrada:
            continue

        cmd = entrada.lower()

        if cmd in {"salir", "exit", "quit"}:
            limpiar_pantalla()
            print("Hasta luego.")
            break

        if cmd in {"gramatica", "gramática", "reglas"}:
            ultima_entrada = entrada
            ultima_respuesta = formatear_gramatica(GRAMATICA)
            ultimo_cambio = ""
            continue

        if cmd == "estado":
            ultima_entrada = entrada
            ultima_respuesta = juego.estado_actual()
            ultimo_cambio = ""
            continue

        if cmd == "debug":
            debug = not debug
            ultima_entrada = entrada
            ultima_respuesta = (
                "Vista técnica activada."
                if debug
                else "Vista técnica desactivada."
            )
            ultimo_cambio = ""
            continue

        ultima_respuesta, ultimo_cambio = procesar_comando(
            juego,
            entrada,
            debug=debug,
        )
        ultima_entrada = entrada

        if juego.estado.terminado:
            mostrar_panel(
                juego,
                ultima_entrada=ultima_entrada,
                ultima_respuesta=ultima_respuesta + "\n\nFin del juego. Has escapado.",
                cambio=ultimo_cambio,
            )
            break


if __name__ == "__main__":
    main()